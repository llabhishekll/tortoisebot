from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    # launch parameters
    use_sim_time = LaunchConfiguration("use_sim_time", default="True")
    port = LaunchConfiguration("port", default="8765")
    address = LaunchConfiguration("address", default="0.0.0.0")

    # package tortoisebot_bringup
    # wraps foxglove_bridge  (ws://0.0.0.0:8765)

    # return launch
    return LaunchDescription(
        [
            DeclareLaunchArgument(name="use_sim_time", default_value="True"),
            DeclareLaunchArgument(name="port", default_value="8765"),
            DeclareLaunchArgument(name="address", default_value="0.0.0.0"),
            Node(
                package="foxglove_bridge",
                executable="foxglove_bridge",
                name="foxglove_bridge_node",
                output="screen",
                parameters=[
                    {
                        "use_sim_time": use_sim_time,
                        "port": port,
                        "address": address,
                    }
                ],
            ),
        ]
    )
