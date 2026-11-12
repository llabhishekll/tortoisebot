from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    ExecuteProcess,
    IncludeLaunchDescription,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    # launch parameters
    use_sim_time = LaunchConfiguration("use_sim_time", default="True")
    ws_port = LaunchConfiguration("ws_port", default="9090")
    video_port = LaunchConfiguration("video_port", default="8080")
    http_port = LaunchConfiguration("http_port", default="8000")
    start_twist_mux = LaunchConfiguration("start_twist_mux", default="True")

    # package tortoisebot_teleop
    path_root = Path(get_package_share_directory("tortoisebot_teleop"))
    path_www = path_root / "www"

    # return launch
    return LaunchDescription(
        [
            DeclareLaunchArgument(name="use_sim_time", default_value="True"),
            DeclareLaunchArgument(name="ws_port", default_value="9090"),
            DeclareLaunchArgument(name="video_port", default_value="8080"),
            DeclareLaunchArgument(name="http_port", default_value="8000"),
            DeclareLaunchArgument(
                name="start_twist_mux",
                default_value="True",
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    (path_root / "launch" / "twist_mux.launch.py").as_posix()
                ),
                launch_arguments={"use_sim_time": use_sim_time}.items(),
                condition=IfCondition(start_twist_mux),
            ),
            Node(
                package="rosbridge_server",
                executable="rosbridge_websocket",
                name="rosbridge_websocket_node",
                output="screen",
                parameters=[
                    {
                        "port": ws_port,
                        "address": "0.0.0.0",
                        "topics_glob": (
                            "[/cmd_vel, /cmd_vel_web, /cmd_vel_key, /odom, /scan]"
                        ),
                        "services_glob": "[]",
                    }
                ],
            ),
            Node(
                package="rosapi",
                executable="rosapi_node",
                name="rosapi_node",
                output="log",
            ),
            Node(
                package="web_video_server",
                executable="web_video_server",
                name="web_video_server_node",
                output="screen",
                parameters=[
                    {
                        "port": video_port,
                        "address": "0.0.0.0",
                    }
                ],
            ),
            ExecuteProcess(
                cmd=[
                    "python3",
                    "-m",
                    "http.server",
                    http_port,
                    "--bind",
                    "0.0.0.0",
                    "--directory",
                    path_www.as_posix(),
                ],
                output="screen",
            ),
        ]
    )
