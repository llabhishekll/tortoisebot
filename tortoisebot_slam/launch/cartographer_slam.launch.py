from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    # launch parameters
    use_sim_time = LaunchConfiguration("use_sim_time", default="True")
    display_rviz = LaunchConfiguration("display_rviz", default="True")
    is_odom_only = LaunchConfiguration("is_odom_only", default="False")
    resolution = LaunchConfiguration("resolution", default="0.05")
    publish_period_sec = LaunchConfiguration("publish_period_sec", default="1.0")

    # package tortoisebot_slam
    path_root = Path(get_package_share_directory("tortoisebot_slam"))
    path_conf = path_root / "config"
    path_rviz = (path_root / "rviz" / "cartographer_slam.config.rviz").as_posix()

    # return launch
    return LaunchDescription(
        [
            DeclareLaunchArgument(name="use_sim_time", default_value="True"),
            DeclareLaunchArgument(name="display_rviz", default_value="True"),
            DeclareLaunchArgument(name="is_odom_only", default_value="False"),
            DeclareLaunchArgument(name="resolution", default_value="0.05"),
            DeclareLaunchArgument(name="publish_period_sec", default_value="1.0"),
            Node(
                package="cartographer_ros",
                executable="cartographer_node",
                name="cartographer_node",
                output="screen",
                arguments=[
                    "-configuration_directory",
                    (path_conf / "sim").as_posix(),
                    "-configuration_basename",
                    "cartographer.config.lua",
                ],
                parameters=[{"use_sim_time": use_sim_time}],
                remappings=[("scan", "/scan"), ("odom", "/odom")],
                condition=IfCondition(use_sim_time),
            ),
            GroupAction(
                condition=UnlessCondition(use_sim_time),
                actions=[
                    Node(
                        package="cartographer_ros",
                        executable="cartographer_node",
                        name="cartographer_node",
                        output="screen",
                        arguments=[
                            "-configuration_directory",
                            (path_conf / "real").as_posix(),
                            "-configuration_basename",
                            "cartographer.config.lua",
                        ],
                        parameters=[{"use_sim_time": use_sim_time}],
                        remappings=[("scan", "/scan"), ("odom", "/odom")],
                        condition=UnlessCondition(is_odom_only),
                    ),
                    Node(
                        package="cartographer_ros",
                        executable="cartographer_node",
                        name="cartographer_node",
                        output="screen",
                        arguments=[
                            "-configuration_directory",
                            (path_conf / "real").as_posix(),
                            "-configuration_basename",
                            "cartographer_odom.config.lua",
                        ],
                        parameters=[{"use_sim_time": use_sim_time}],
                        remappings=[("scan", "/scan"), ("odom", "/odom")],
                        condition=IfCondition(is_odom_only),
                    ),
                ],
            ),
            Node(
                package="cartographer_ros",
                executable="cartographer_occupancy_grid_node",
                name="cartographer_occupancy_grid_node",
                output="screen",
                arguments=[
                    "-resolution",
                    resolution,
                    "-publish_period_sec",
                    publish_period_sec,
                ],
                parameters=[{"use_sim_time": use_sim_time}],
                condition=UnlessCondition(is_odom_only),
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
