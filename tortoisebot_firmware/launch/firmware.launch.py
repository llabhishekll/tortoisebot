from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    # launch parameters
    use_sim_time = LaunchConfiguration("use_sim_time", default="False")
    backend = LaunchConfiguration("backend", default="auto")

    # return launch
    return LaunchDescription(
        [
            DeclareLaunchArgument(name="use_sim_time", default_value="False"),
            DeclareLaunchArgument(name="backend", default_value="auto"),
            Node(
                package="tortoisebot_firmware",
                executable="differential",
                name="differential_node",
                output="screen",
                parameters=[
                    {
                        "use_sim_time": use_sim_time,
                        "backend": backend,
                    }
                ],
            ),
        ]
    )
