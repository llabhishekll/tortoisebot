from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    # launch parameters
    use_sim_time = LaunchConfiguration("use_sim_time", default="True")
    map_name = LaunchConfiguration("map_name")

    # save into navigation maps (where Nav2 loads from)
    path_nav = Path(get_package_share_directory("tortoisebot_navigation"))
    default_map = (path_nav / "maps" / "room_map_sim").as_posix()

    # return launch
    return LaunchDescription(
        [
            DeclareLaunchArgument(name="use_sim_time", default_value="True"),
            DeclareLaunchArgument(name="map_name", default_value=default_map),
            Node(
                package="nav2_map_server",
                executable="map_saver_cli",
                name="map_saver_node",
                output="screen",
                arguments=["-f", map_name],
                parameters=[{"use_sim_time": use_sim_time}],
            ),
        ]
    )
