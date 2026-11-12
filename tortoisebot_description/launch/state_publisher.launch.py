from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.descriptions import ParameterValue


def generate_launch_description():
    # launch parameters
    use_sim_time = LaunchConfiguration("use_sim_time", default="False")

    # package tortoisebot_description
    path_root = Path(get_package_share_directory("tortoisebot_description"))
    path_sim = (path_root / "models" / "urdf" / "tortoisebot_sim.xacro").as_posix()
    path_real = (path_root / "models" / "urdf" / "tortoisebot_real.xacro").as_posix()

    # return launch
    return LaunchDescription(
        [
            DeclareLaunchArgument(name="use_sim_time", default_value="False"),
            Node(
                package="robot_state_publisher",
                executable="robot_state_publisher",
                name="robot_state_publisher",
                output="screen",
                parameters=[
                    {
                        "use_sim_time": use_sim_time,
                        "robot_description": ParameterValue(
                            Command(["xacro ", path_sim]),
                            value_type=str,
                        ),
                        "publish_frequency": 50.0,
                    }
                ],
                condition=IfCondition(use_sim_time),
            ),
            Node(
                package="robot_state_publisher",
                executable="robot_state_publisher",
                name="robot_state_publisher",
                output="screen",
                parameters=[
                    {
                        "use_sim_time": use_sim_time,
                        "robot_description": ParameterValue(
                            Command(["xacro ", path_real]),
                            value_type=str,
                        ),
                        "publish_frequency": 50.0,
                    }
                ],
                condition=UnlessCondition(use_sim_time),
            ),
            Node(
                package="joint_state_publisher",
                executable="joint_state_publisher",
                name="joint_state_publisher",
                parameters=[{"use_sim_time": use_sim_time}],
                condition=UnlessCondition(use_sim_time),
            ),
        ]
    )
