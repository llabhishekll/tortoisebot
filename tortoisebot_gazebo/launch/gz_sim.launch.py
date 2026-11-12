import os
from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    SetEnvironmentVariable,
    TimerAction,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    # launch parameters
    world = LaunchConfiguration("world")
    spawn_x = LaunchConfiguration("spawn_x", default="0.0")
    spawn_y = LaunchConfiguration("spawn_y", default="0.0")

    # package tortoisebot_gazebo
    path_desc = Path(get_package_share_directory("tortoisebot_description"))
    path_gazebo = Path(get_package_share_directory("tortoisebot_gazebo"))
    path_ros_gz = Path(get_package_share_directory("ros_gz_sim"))
    default_world = (path_gazebo / "worlds" / "room.sdf").as_posix()

    # workspace + active ROS share (from sourced prefix), plus any existing path
    resource_parts = [
        str(path_desc),
        str(path_desc.parent),
        str(path_gazebo),
        str(path_gazebo.parent),
        str(path_ros_gz.parent),
    ]
    for prefix in os.environ.get("AMENT_PREFIX_PATH", "").split(":"):
        if not prefix:
            continue
        share = str(Path(prefix) / "share")
        if share not in resource_parts:
            resource_parts.append(share)
    existing = os.environ.get("GZ_SIM_RESOURCE_PATH", "")
    if existing:
        resource_parts.append(existing)
    resource_path = ":".join(resource_parts)

    # return launch
    return LaunchDescription(
        [
            DeclareLaunchArgument(name="world", default_value=default_world),
            DeclareLaunchArgument(name="spawn_x", default_value="0.0"),
            DeclareLaunchArgument(name="spawn_y", default_value="0.0"),
            SetEnvironmentVariable(
                name="GZ_SIM_RESOURCE_PATH",
                value=resource_path,
            ),
            Node(
                package="ros_gz_bridge",
                executable="parameter_bridge",
                name="gz_bridge_node",
                output="screen",
                arguments=[
                    "/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist",
                    "/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry",
                    "/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock",
                    "/model/tortoisebot/tf@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V",
                    "/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan",
                    "/camera/image_raw@sensor_msgs/msg/Image[gz.msgs.Image",
                    "/camera/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo",
                ],
                remappings=[
                    ("/model/tortoisebot/tf", "/tf"),
                ],
                parameters=[
                    {
                        "use_sim_time": True,
                        "qos_overrides./tf_static.publisher.durability": "transient_local",
                        "qos_overrides./scan.publisher.reliability": "reliable",
                        "qos_overrides./odom.publisher.reliability": "reliable",
                    }
                ],
            ),
            Node(
                package="ros_gz_bridge",
                executable="parameter_bridge",
                name="joint_state_bridge_node",
                output="screen",
                arguments=[
                    "/world/default/model/tortoisebot/joint_state"
                    "@sensor_msgs/msg/JointState[gz.msgs.Model"
                ],
                remappings=[
                    (
                        "/world/default/model/tortoisebot/joint_state",
                        "/joint_states",
                    )
                ],
                parameters=[{"use_sim_time": True}],
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    (path_ros_gz / "launch" / "gz_sim.launch.py").as_posix()
                ),
                launch_arguments={
                    "gz_args": ["-r ", world],
                    "on_exit_shutdown": "true",
                }.items(),
            ),
            TimerAction(
                period=2.0,
                actions=[
                    Node(
                        package="ros_gz_sim",
                        executable="create",
                        name="gz_spawn_node",
                        output="screen",
                        arguments=[
                            "-name",
                            "tortoisebot",
                            "-topic",
                            "robot_description",
                            "-x",
                            spawn_x,
                            "-y",
                            spawn_y,
                            "-z",
                            "0.01",
                        ],
                    )
                ],
            ),
        ]
    )
