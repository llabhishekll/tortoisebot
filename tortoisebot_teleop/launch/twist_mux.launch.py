from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    # launch parameters
    use_sim_time = LaunchConfiguration("use_sim_time", default="True")

    # package tortoisebot_teleop
    path_teleop = Path(get_package_share_directory("tortoisebot_teleop"))
    path_config = (path_teleop / "config" / "twist_mux.config.yml").as_posix()

    # return launch
    return LaunchDescription(
        [
            DeclareLaunchArgument(name="use_sim_time", default_value="True"),
            Node(
                package="twist_mux",
                executable="twist_mux",
                name="twist_mux_node",
                output="screen",
                parameters=[
                    path_config,
                    {"use_sim_time": use_sim_time},
                ],
                remappings=[
                    ("cmd_vel_out", "/cmd_vel"),
                ],
            ),
        ]
    )
