from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    # launch parameters
    use_sim_time = LaunchConfiguration("use_sim_time", default="True")
    image_topic = LaunchConfiguration("image_topic", default="/camera/image_raw")
    score_threshold = LaunchConfiguration("score_threshold", default="0.5")

    # package tortoisebot_intelligence

    # return launch
    return LaunchDescription(
        [
            DeclareLaunchArgument(name="use_sim_time", default_value="True"),
            DeclareLaunchArgument(
                name="image_topic", default_value="/camera/image_raw"
            ),
            DeclareLaunchArgument(name="score_threshold", default_value="0.5"),
            Node(
                package="tortoisebot_intelligence",
                executable="detector",
                name="detector_node",
                output="screen",
                parameters=[
                    {
                        "use_sim_time": use_sim_time,
                        "image_topic": image_topic,
                        "score_threshold": score_threshold,
                    }
                ],
            ),
        ]
    )
