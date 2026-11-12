#!/usr/bin/env python3
"""Publish /intelligence/status and /intelligence/detections from camera."""

import contextlib
import json
from pathlib import Path

import rclpy
from ament_index_python.packages import get_package_share_directory
from rcl_interfaces.msg import SetParametersResult
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String


class DetectorNode(Node):
    def __init__(self):
        super().__init__("detector_node")
        # member variables
        self.model = None
        self.last_image_time = None
        self.last_detections = []

        # node parameters
        self.use_sim_time = self.get_parameter("use_sim_time").value
        self.image_topic = self.declare_parameter(
            "image_topic", "/camera/image_raw"
        ).value
        default_model = str(
            Path(get_package_share_directory("tortoisebot_intelligence"))
            / "models"
            / "detector.onnx"
        )
        self.model_path = self.declare_parameter("model_path", default_model).value
        self.node_rate = self.declare_parameter("node_rate", 5.0).value
        self.score_threshold = self.declare_parameter("score_threshold", 0.5).value

        # ros objects
        self.subscriber_image = self.create_subscription(
            Image, self.image_topic, self.subscriber_image_callback, 10
        )
        self.publisher_status = self.create_publisher(
            String, "/intelligence/status", 10
        )
        self.publisher_detections = self.create_publisher(
            String, "/intelligence/detections", 10
        )
        self.timer_status = self.create_timer(
            1.0 / self.node_rate, self.timer_status_callback
        )

        # parameter handler
        self.add_on_set_parameters_callback(self.on_parameter_changed)

        self.load_model()
        self.get_logger().info(
            f"Detector node started successfully. image_topic={self.image_topic}"
        )

    def on_parameter_changed(self, params):
        for param in params:
            if hasattr(self, param.name):
                current_value = getattr(self, param.name)
                if current_value != param.value:
                    self.get_logger().info(
                        f"Parameter '{param.name}' changed from "
                        f"{current_value} to {param.value}"
                    )
                    setattr(self, param.name, param.value)
                    if param.name == "model_path":
                        self.load_model()
            else:
                self.get_logger().warning(
                    f"Attempting to set an unknown parameter '{param.name}'"
                )
        return SetParametersResult(successful=True)

    def load_model(self):
        self.model = None
        model_file = Path(self.model_path)
        if not model_file.is_file():
            self.get_logger().error(f"Model not found: {model_file}")
            return
        self.model = model_file
        self.get_logger().info(f"Model loaded: {model_file}")

    def subscriber_image_callback(self, message):
        self.last_image_time = self.get_clock().now()
        self.last_detections = self.run_inference(message)

    def run_inference(self, _message):
        if self.model is None:
            return []
        return []

    def timer_status_callback(self):
        if self.model is None:
            state = "error"
        elif self.last_image_time is None:
            state = "waiting_for_image"
        else:
            state = "running"

        status = String()
        status.data = state
        self.publisher_status.publish(status)

        detections = String()
        detections.data = json.dumps(
            {
                "score_threshold": self.score_threshold,
                "detections": self.last_detections,
            }
        )
        self.publisher_detections.publish(detections)


def main(args=None):
    # initialize ros, executor and node
    rclpy.init(args=args)
    node = DetectorNode()

    with contextlib.suppress(KeyboardInterrupt):
        rclpy.spin(node)

    # shutdown
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
