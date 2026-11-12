from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    OpaqueFunction,
)
from launch.conditions import IfCondition, UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def _ensure_rviz_home(context, *args, **kwargs):
    Path.home().joinpath(".rviz2").mkdir(parents=True, exist_ok=True)
    return []


def generate_launch_description():
    # launch parameters
    use_sim_time = LaunchConfiguration("use_sim_time", default="True")
    camera_port = LaunchConfiguration("camera_port", default="0")
    display_rviz = LaunchConfiguration("display_rviz", default="True")
    extras = LaunchConfiguration("extras", default="True")

    # package tortoisebot_bringup
    path_desc = Path(get_package_share_directory("tortoisebot_description"))
    path_gazebo = Path(get_package_share_directory("tortoisebot_gazebo"))
    path_lidar = Path(get_package_share_directory("ydlidar_ros2_driver"))
    path_bringup = Path(get_package_share_directory("tortoisebot_bringup"))
    path_teleop = Path(get_package_share_directory("tortoisebot_teleop"))

    world_file = (path_gazebo / "worlds" / "room.sdf").as_posix()
    lidar_params = (path_lidar / "params" / "ydlidar.yaml").as_posix()
    path_rviz = (path_bringup / "rviz" / "robot.config.rviz").as_posix()

    # return launch
    return LaunchDescription(
        [
            DeclareLaunchArgument(name="use_sim_time", default_value="True"),
            DeclareLaunchArgument(name="camera_port", default_value="0"),
            DeclareLaunchArgument(
                name="display_rviz",
                default_value="True",
                description="Start RViz2 with robot.config.rviz",
            ),
            DeclareLaunchArgument(
                name="extras",
                default_value="True",
                description="Start Foxglove bridge and web teleop",
            ),
            OpaqueFunction(function=_ensure_rviz_home),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    (path_desc / "launch" / "state_publisher.launch.py").as_posix()
                ),
                launch_arguments={"use_sim_time": use_sim_time}.items(),
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    (path_gazebo / "launch" / "gz_sim.launch.py").as_posix()
                ),
                launch_arguments={
                    "world": world_file,
                    "spawn_x": "0.0",
                    "spawn_y": "0.0",
                }.items(),
                condition=IfCondition(use_sim_time),
            ),
            Node(
                package="ydlidar_ros2_driver",
                executable="ydlidar_ros2_driver_node",
                name="ydlidar_ros2_driver_node",
                output="screen",
                parameters=[
                    lidar_params,
                    {"frame_id": "robot_front_laser_base_link"},
                ],
                condition=UnlessCondition(use_sim_time),
            ),
            Node(
                package="tortoisebot_firmware",
                executable="differential",
                name="differential_node",
                output="screen",
                parameters=[
                    {
                        "use_sim_time": False,
                        "backend": "auto",
                    }
                ],
                condition=UnlessCondition(use_sim_time),
            ),
            Node(
                package="camera_ros",
                executable="camera_node",
                name="camera_node",
                output="screen",
                parameters=[
                    {
                        "camera": camera_port,
                        "format": "RGB888",
                        "width": 800,
                        "height": 600,
                    }
                ],
                remappings=[
                    ("~/image_raw", "/camera/image_raw"),
                    ("~/camera_info", "/camera/camera_info"),
                ],
                condition=UnlessCondition(use_sim_time),
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    (path_teleop / "launch" / "twist_mux.launch.py").as_posix()
                ),
                launch_arguments={"use_sim_time": use_sim_time}.items(),
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    (path_bringup / "launch" / "foxglove.launch.py").as_posix()
                ),
                launch_arguments={"use_sim_time": use_sim_time}.items(),
                condition=IfCondition(extras),
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    (path_teleop / "launch" / "teleop_web.launch.py").as_posix()
                ),
                launch_arguments={
                    "use_sim_time": use_sim_time,
                    "start_twist_mux": "False",
                }.items(),
                condition=IfCondition(extras),
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
