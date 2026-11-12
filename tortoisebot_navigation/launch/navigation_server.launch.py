from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    GroupAction,
    IncludeLaunchDescription,
    TimerAction,
)
from launch.conditions import IfCondition, UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
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
    path_slam = Path(get_package_share_directory("tortoisebot_slam"))
    path_sim = path_root / "config" / "sim"
    path_real = path_root / "config" / "real"
    path_bt_to_pose = (path_root / "config" / "to_pose.xml").as_posix()
    path_bt_through_poses = (path_root / "config" / "through_poses.xml").as_posix()
    default_map = (path_root / "maps" / "room_map_sim.yaml").as_posix()
    path_rviz = (path_root / "rviz" / "navigation_server.config.rviz").as_posix()

    nav_server_nodes = [
        "planner_server_node",
        "smoother_server_node",
        "controller_server_node",
        "behavior_server_node",
        "waypoint_follower_node",
        "velocity_smoother_node",
    ]
    bt_nodes = [
        "bt_navigator_node",
    ]
    planner_remappings = []
    controller_remappings = [
        ("cmd_vel", "cmd_vel_nav"),
    ]
    behavior_remappings = [
        ("cmd_vel", "cmd_vel_nav"),
    ]
    bt_rewrites = {
        "default_nav_to_pose_bt_xml": path_bt_to_pose,
        "default_nav_through_poses_bt_xml": path_bt_through_poses,
    }

    # return launch
    return LaunchDescription(
        [
            DeclareLaunchArgument(name="use_sim_time", default_value="True"),
            DeclareLaunchArgument(name="display_rviz", default_value="True"),
            DeclareLaunchArgument(name="map_file", default_value=default_map),
            # Real robot: Cartographer odom-only (no wheel encoders).
            # Scoped GroupAction so child display_rviz:=False does not overwrite
            # this launch's display_rviz (otherwise parent RViz never starts).
            GroupAction(
                actions=[
                    IncludeLaunchDescription(
                        PythonLaunchDescriptionSource(
                            (
                                path_slam / "launch" / "cartographer_slam.launch.py"
                            ).as_posix()
                        ),
                        launch_arguments={
                            "use_sim_time": use_sim_time,
                            "is_odom_only": "True",
                            "display_rviz": "False",
                        }.items(),
                    ),
                ],
                scoped=True,
                condition=UnlessCondition(use_sim_time),
            ),
            GroupAction(
                actions=[
                    IncludeLaunchDescription(
                        PythonLaunchDescriptionSource(
                            (
                                path_root / "launch" / "localization_server.launch.py"
                            ).as_posix()
                        ),
                        launch_arguments={
                            "use_sim_time": use_sim_time,
                            "map_file": map_file,
                            "display_rviz": "False",
                        }.items(),
                    ),
                ],
                scoped=True,
            ),
            Node(
                package="nav2_planner",
                executable="planner_server",
                name="planner_server_node",
                output="screen",
                parameters=[
                    generate_yaml_param(path_sim / "planner_server.config.yml")
                ],
                remappings=planner_remappings,
                condition=IfCondition(use_sim_time),
            ),
            Node(
                package="nav2_planner",
                executable="planner_server",
                name="planner_server_node",
                output="screen",
                parameters=[
                    generate_yaml_param(path_real / "planner_server.config.yml")
                ],
                remappings=planner_remappings,
                condition=UnlessCondition(use_sim_time),
            ),
            Node(
                package="nav2_smoother",
                executable="smoother_server",
                name="smoother_server_node",
                output="screen",
                parameters=[
                    generate_yaml_param(path_sim / "smoother_server.config.yml")
                ],
                condition=IfCondition(use_sim_time),
            ),
            Node(
                package="nav2_smoother",
                executable="smoother_server",
                name="smoother_server_node",
                output="screen",
                parameters=[
                    generate_yaml_param(path_real / "smoother_server.config.yml")
                ],
                condition=UnlessCondition(use_sim_time),
            ),
            Node(
                package="nav2_controller",
                executable="controller_server",
                name="controller_server_node",
                output="screen",
                parameters=[
                    generate_yaml_param(path_sim / "controller_server.config.yml")
                ],
                remappings=controller_remappings,
                condition=IfCondition(use_sim_time),
            ),
            Node(
                package="nav2_controller",
                executable="controller_server",
                name="controller_server_node",
                output="screen",
                parameters=[
                    generate_yaml_param(path_real / "controller_server.config.yml")
                ],
                remappings=controller_remappings,
                condition=UnlessCondition(use_sim_time),
            ),
            Node(
                package="nav2_behaviors",
                executable="behavior_server",
                name="behavior_server_node",
                output="screen",
                parameters=[
                    generate_yaml_param(path_sim / "behavior_server.config.yml")
                ],
                remappings=behavior_remappings,
                condition=IfCondition(use_sim_time),
            ),
            Node(
                package="nav2_behaviors",
                executable="behavior_server",
                name="behavior_server_node",
                output="screen",
                parameters=[
                    generate_yaml_param(path_real / "behavior_server.config.yml")
                ],
                remappings=behavior_remappings,
                condition=UnlessCondition(use_sim_time),
            ),
            Node(
                package="nav2_bt_navigator",
                executable="bt_navigator",
                name="bt_navigator_node",
                output="screen",
                parameters=[
                    generate_yaml_param(
                        path_sim / "behavior_tree.config.yml",
                        bt_rewrites,
                    )
                ],
                condition=IfCondition(use_sim_time),
            ),
            Node(
                package="nav2_bt_navigator",
                executable="bt_navigator",
                name="bt_navigator_node",
                output="screen",
                parameters=[
                    generate_yaml_param(
                        path_real / "behavior_tree.config.yml",
                        bt_rewrites,
                    )
                ],
                condition=UnlessCondition(use_sim_time),
            ),
            Node(
                package="nav2_waypoint_follower",
                executable="waypoint_follower",
                name="waypoint_follower_node",
                output="screen",
                parameters=[
                    generate_yaml_param(path_sim / "waypoint_follower.config.yml")
                ],
                condition=IfCondition(use_sim_time),
            ),
            Node(
                package="nav2_waypoint_follower",
                executable="waypoint_follower",
                name="waypoint_follower_node",
                output="screen",
                parameters=[
                    generate_yaml_param(path_real / "waypoint_follower.config.yml")
                ],
                condition=UnlessCondition(use_sim_time),
            ),
            Node(
                package="nav2_velocity_smoother",
                executable="velocity_smoother",
                name="velocity_smoother_node",
                output="screen",
                parameters=[
                    generate_yaml_param(path_sim / "velocity_smoother.config.yml")
                ],
                remappings=[
                    ("cmd_vel", "cmd_vel_nav"),
                    ("cmd_vel_smoothed", "/cmd_vel_nav2"),
                ],
                condition=IfCondition(use_sim_time),
            ),
            Node(
                package="nav2_velocity_smoother",
                executable="velocity_smoother",
                name="velocity_smoother_node",
                output="screen",
                parameters=[
                    generate_yaml_param(path_real / "velocity_smoother.config.yml")
                ],
                remappings=[
                    ("cmd_vel", "cmd_vel_nav"),
                    ("cmd_vel_smoothed", "/cmd_vel_nav2"),
                ],
                condition=UnlessCondition(use_sim_time),
            ),
            TimerAction(
                period=8.0,
                actions=[
                    Node(
                        package="nav2_lifecycle_manager",
                        executable="lifecycle_manager",
                        name="navigation_manager_node",
                        output="screen",
                        parameters=[
                            {
                                "use_sim_time": use_sim_time,
                                "autostart": True,
                                "bond_timeout": 0.0,
                                "node_names": list(nav_server_nodes),
                            }
                        ],
                    )
                ],
            ),
            TimerAction(
                period=15.0,
                actions=[
                    Node(
                        package="nav2_lifecycle_manager",
                        executable="lifecycle_manager",
                        name="bt_manager_node",
                        output="screen",
                        parameters=[
                            {
                                "use_sim_time": use_sim_time,
                                "autostart": True,
                                "bond_timeout": 0.0,
                                "node_names": list(bt_nodes),
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
