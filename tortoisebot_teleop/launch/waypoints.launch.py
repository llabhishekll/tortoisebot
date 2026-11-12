from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    # launch parameters
    use_sim_time = LaunchConfiguration("use_sim_time", default="True")
    route = LaunchConfiguration("route", default="patrol")
    yaml_filename = LaunchConfiguration("yaml_filename")

    # package tortoisebot_teleop
    path_root = Path(get_package_share_directory("tortoisebot_teleop"))
    default_yaml = (path_root / "config" / "waypoints.yaml").as_posix()

    # return launch
    return LaunchDescription(
        [
            DeclareLaunchArgument(name="use_sim_time", default_value="True"),
            DeclareLaunchArgument(name="route", default_value="patrol"),
            DeclareLaunchArgument(name="yaml_filename", default_value=default_yaml),
            Node(
                package="tortoisebot_teleop",
                executable="waypoints",
                name="waypoint_follower_client_node",
                output="screen",
                parameters=[
                    {
                        "use_sim_time": use_sim_time,
                        "yaml_filename": yaml_filename,
                        "route": route,
                    }
                ],
            ),
        ]
    )
