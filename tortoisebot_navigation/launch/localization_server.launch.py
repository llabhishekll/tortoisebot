from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, TimerAction
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from nav2_common.launch import RewrittenYaml


def generate_yaml_param(path, param_rewrites=None):
    # dynamic substitutions for parameters
    return RewrittenYaml(
        source_file=path.as_posix(),
        param_rewrites=param_rewrites or {},
    )


def generate_launch_description():
    # launch parameters
    use_sim_time = LaunchConfiguration("use_sim_time", default="True")
    display_rviz = LaunchConfiguration("display_rviz", default="True")
    map_file = LaunchConfiguration("map_file")

    # package tortoisebot_navigation
    path_root = Path(get_package_share_directory("tortoisebot_navigation"))
    path_sim = path_root / "config" / "sim"
    path_real = path_root / "config" / "real"
    default_map = (path_root / "maps" / "room_map_sim.yaml").as_posix()
    path_rviz = (path_root / "rviz" / "localization_server.config.rviz").as_posix()

    # return launch
    return LaunchDescription(
        [
            DeclareLaunchArgument(name="use_sim_time", default_value="True"),
            DeclareLaunchArgument(name="display_rviz", default_value="True"),
            DeclareLaunchArgument(name="map_file", default_value=default_map),
            Node(
                package="nav2_map_server",
                executable="map_server",
                name="map_server_node",
                output="screen",
                parameters=[
                    {
                        "use_sim_time": use_sim_time,
                        "yaml_filename": map_file,
                        "use_bond": False,
                    }
                ],
            ),
            Node(
                package="nav2_amcl",
                executable="amcl",
                name="localization_node",
                output="screen",
                parameters=[
                    generate_yaml_param(path_sim / "localization_server.config.yml")
                ],
                remappings=[("scan", "/scan")],
                condition=IfCondition(use_sim_time),
            ),
            Node(
                package="nav2_amcl",
                executable="amcl",
                name="localization_node",
                output="screen",
                parameters=[
                    generate_yaml_param(path_real / "localization_server.config.yml")
                ],
                remappings=[("scan", "/scan")],
                condition=UnlessCondition(use_sim_time),
            ),
            TimerAction(
                period=5.0,
                actions=[
                    Node(
                        package="nav2_lifecycle_manager",
                        executable="lifecycle_manager",
                        name="localization_manager_node",
                        output="screen",
                        parameters=[
                            {
                                "use_sim_time": use_sim_time,
                                "autostart": True,
                                "bond_timeout": 0.0,
                                "node_names": [
                                    "map_server_node",
                                    "localization_node",
                                ],
                            }
                        ],
                    )
                ],
            ),
            Node(
                package="rviz2",
                executable="rviz2",
                name="rviz_node",
                output="screen",
                arguments=["-d", path_rviz],
                parameters=[{"use_sim_time": use_sim_time}],
                condition=IfCondition(display_rviz),
            ),
        ]
    )
