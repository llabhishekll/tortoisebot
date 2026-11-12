#!/usr/bin/env python3
"""Send FollowWaypoints goals from a YAML route (teleop / patrol helper)."""

import math
from pathlib import Path

import rclpy
import yaml
from geometry_msgs.msg import PoseStamped, Quaternion
from nav2_msgs.action import FollowWaypoints
from rcl_interfaces.msg import SetParametersResult
from rclpy.action import ActionClient
from rclpy.node import Node


class WaypointFollowerNode(Node):
    def __init__(self):
        super().__init__("waypoint_follower_client_node")
        # member variables
        self.waypoints = []

        # node parameters
        self.use_sim_time = self.get_parameter("use_sim_time").value
        self.yaml_filename = self.declare_parameter("yaml_filename", "/").value
        self.route = self.declare_parameter("route", "patrol").value

        # ros objects
        self.client_waypoints = ActionClient(self, FollowWaypoints, "follow_waypoints")

        # parameter handler
        self.add_on_set_parameters_callback(self.on_parameter_changed)

        # load yaml after parameters exist
        self.waypoints = self.load_waypoints_yaml(self.yaml_filename, self.route)
        self.get_logger().info(
            f"Waypoint node started successfully. route={self.route} count={len(self.waypoints)}"
        )

    def on_parameter_changed(self, params):
        for param in params:
            if hasattr(self, param.name):
                current_value = getattr(self, param.name)
                if current_value != param.value:
                    self.get_logger().info(
                        f"Parameter '{param.name}' changed from {current_value} to {param.value}"
                    )
                    setattr(self, param.name, param.value)
            else:
                self.get_logger().warning(
                    f"Attempting to set an unknown parameter '{param.name}'"
                )
        return SetParametersResult(successful=True)

    def load_waypoints_yaml(self, yaml_filename, route):
        poses = []
        try:
            with Path(yaml_filename).open() as handle:
                data = yaml.safe_load(handle)
        except Exception as exc:
            self.get_logger().error(f"Could not read waypoints yaml: {exc}")
            return poses

        # simulation vs real waypoint lists in the yaml
        section = "simulation" if self.use_sim_time else "real"
        points = data.get(section, {}).get(route, [])
        for item in points:
            pose = PoseStamped()
            pose.header.stamp = self.get_clock().now().to_msg()
            pose.header.frame_id = "map"
            pose.pose.position.x = float(item[0])
            pose.pose.position.y = float(item[1])
            pose.pose.position.z = 0.0
            pose.pose.orientation = self.yaw_to_quaternion(float(item[2]))
            poses.append(pose)
        return poses

    def yaw_to_quaternion(self, yaw):
        orientation = Quaternion()
        orientation.x = 0.0
        orientation.y = 0.0
        orientation.z = math.sin(yaw / 2.0)
        orientation.w = math.cos(yaw / 2.0)
        return orientation

    def send_goal(self):
        if not self.waypoints:
            self.get_logger().error("No waypoints loaded.")
            return

        goal_msg = FollowWaypoints.Goal()
        goal_msg.poses = self.waypoints
        self.client_waypoints.wait_for_server()
        send_future = self.client_waypoints.send_goal_async(
            goal_msg, feedback_callback=self.feedback_callback
        )
        send_future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().info("Goal rejected")
            return

        self.get_logger().info("Goal Accepted")
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self.get_result_callback)

    def get_result_callback(self, future):
        result = future.result().result
        self.get_logger().info(
            f"Result -> Missed Waypoints: {len(result.missed_waypoints)}"
        )
        rclpy.shutdown()

    def feedback_callback(self, feedback_msg):
        feedback = feedback_msg.feedback
        self.get_logger().info(
            f"Feedback -> Current Waypoint: {feedback.current_waypoint}",
            throttle_duration_sec=2.0,
        )


def main(args=None):
    # initialize ros, executor and node
    rclpy.init(args=args)
    node = WaypointFollowerNode()
    node.send_goal()
    rclpy.spin(node)

    # shutdown
    rclpy.shutdown()


if __name__ == "__main__":
    main()
