from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    # launch parameters
    use_sim_time = LaunchConfiguration("use_sim_time", default="True")
    display_rviz = LaunchConfiguration("display_rviz", default="True")
    map_file = LaunchConfiguration("map_file")

    # package tortoisebot_navigation
    path_root = Path(get_package_share_directory("tortoisebot_navigation"))
    default_map = (path_root / "maps" / "room_map_sim.yaml").as_posix()
    path_rviz = (path_root / "rviz" / "map_server.config.rviz").as_posix()

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
                    }
                ],
            ),
            Node(
                package="nav2_lifecycle_manager",
                executable="lifecycle_manager",
                name="map_manager_node",
                output="screen",
                parameters=[
                    {
                        "use_sim_time": use_sim_time,
                        "autostart": True,
                        "node_names": ["map_server_node"],
                    }
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
