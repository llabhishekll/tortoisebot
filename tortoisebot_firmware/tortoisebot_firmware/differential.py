#!/usr/bin/env python3
"""Drive L298N motors from /cmd_vel (GPIO on Pi, mock on laptop)."""

import contextlib
import math

import rclpy
from geometry_msgs.msg import Twist
from rcl_interfaces.msg import SetParametersResult
from rclpy.node import Node
from std_msgs.msg import Bool, Int32

# raspberry pi gpio is optional; laptop uses mock backend
try:
    import RPi.GPIO as GPIO  # ty: ignore[unresolved-import]

    GPIO_AVAILABLE = True
except ImportError:
    GPIO = None
    GPIO_AVAILABLE = False


class DifferentialDriveNode(Node):
    def __init__(self):
        super().__init__("differential_node")
        # member variables
        self.pwm_left = None
        self.pwm_right = None
        self.connected = False
        self.last_cmd_time = None

        # node parameters
        self.use_sim_time = self.get_parameter("use_sim_time").value
        self.backend = self.declare_parameter("backend", "auto").value
        self.wheel_diameter = self.declare_parameter("wheel_diameter", 0.065).value
        self.wheel_separation = self.declare_parameter(
            "wheel_separation", 0.17186
        ).value
        self.motor_rpm = self.declare_parameter("motor_rpm", 60.0).value
        self.max_pwm = self.declare_parameter("max_pwm", 100.0).value
        self.min_pwm = self.declare_parameter("min_pwm", 15.0).value
        self.cmd_vel_timeout = self.declare_parameter("cmd_vel_timeout", 0.5).value
        self.pwm_frequency = self.declare_parameter("pwm_frequency", 100).value
        self.left_en_pin = self.declare_parameter("left_en_pin", 13).value
        self.right_en_pin = self.declare_parameter("right_en_pin", 12).value
        self.left_forward_pin = self.declare_parameter("left_forward_pin", 6).value
        self.left_backward_pin = self.declare_parameter("left_backward_pin", 5).value
        self.right_forward_pin = self.declare_parameter("right_forward_pin", 16).value
        self.right_backward_pin = self.declare_parameter("right_backward_pin", 20).value

        # node modification
        self.wheel_radius = self.wheel_diameter / 2.0
        self.circumference = 2.0 * math.pi * self.wheel_radius
        self.max_speed = (self.circumference * self.motor_rpm) / 60.0
        self.backend = self.resolve_backend(self.backend)

        # ros objects
        self.subscriber_cmd = self.create_subscription(
            Twist, "/cmd_vel", self.subscriber_cmd_callback, 10
        )
        self.publisher_lpwm = self.create_publisher(Int32, "/lpwm", 10)
        self.publisher_rpwm = self.create_publisher(Int32, "/rpwm", 10)
        self.publisher_ldir = self.create_publisher(Bool, "/ldir", 10)
        self.publisher_rdir = self.create_publisher(Bool, "/rdir", 10)
        self.timer_watchdog = self.create_timer(0.1, self.timer_watchdog_callback)

        # parameter handler
        self.add_on_set_parameters_callback(self.on_parameter_changed)

        # connect after parameters exist (never at import time)
        self.connect_motors()
        self.get_logger().info(
            f"Differential node started successfully. backend={self.backend} max_speed={self.max_speed:.3f} m/s"
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

    def resolve_backend(self, backend):
        # auto: gpio on the robot, mock on a pc
        if backend == "auto":
            return "gpio" if GPIO_AVAILABLE else "mock"
        return backend

    def connect_motors(self):
        if self.backend == "mock":
            self.connected = True
            self.get_logger().info("Using mock motor backend (no GPIO).")
            return

        if GPIO is None:
            self.get_logger().error("RPi.GPIO is not available, falling back to mock.")
            self.backend = "mock"
            self.connected = True
            return

        # configure raspberry pi pins only when the node starts
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.left_en_pin, GPIO.OUT)
        GPIO.setup(self.right_en_pin, GPIO.OUT)
        GPIO.setup(self.left_forward_pin, GPIO.OUT)
        GPIO.setup(self.left_backward_pin, GPIO.OUT)
        GPIO.setup(self.right_forward_pin, GPIO.OUT)
        GPIO.setup(self.right_backward_pin, GPIO.OUT)
        self.pwm_left = GPIO.PWM(self.left_en_pin, self.pwm_frequency)
        self.pwm_right = GPIO.PWM(self.right_en_pin, self.pwm_frequency)
        self.pwm_left.start(0)
        self.pwm_right.start(0)
        self.connected = True

    def subscriber_cmd_callback(self, message):
        self.last_cmd_time = self.get_clock().now()

        # inverse kinematics: twist -> left / right ground speed
        linear_vel = message.linear.x
        angular_vel = message.angular.z
        vr_plus_vl = 2.0 * linear_vel
        vr_minus_vl = angular_vel * self.wheel_separation
        right_vel = (vr_plus_vl + vr_minus_vl) / 2.0
        left_vel = vr_plus_vl - right_vel

        if left_vel == 0.0 and right_vel == 0.0:
            self.stop_motors()
            return

        self.apply_wheel_speeds(left_vel, right_vel)

    def timer_watchdog_callback(self):
        # stop if nav / teleop dies and stops publishing
        if self.last_cmd_time is None:
            return
        elapsed = (self.get_clock().now() - self.last_cmd_time).nanoseconds / 1e9
        if elapsed > self.cmd_vel_timeout:
            self.stop_motors()
            self.last_cmd_time = None
            self.get_logger().warning(
                "cmd_vel timeout, motors stopped.",
                skip_first=True,
                throttle_duration_sec=2.0,
            )

    def apply_wheel_speeds(self, left_speed, right_speed):
        left_pwm = self.speed_to_pwm(left_speed)
        right_pwm = self.speed_to_pwm(right_speed)

        if self.backend == "gpio" and self.pwm_left and self.pwm_right:
            self.pwm_left.ChangeDutyCycle(left_pwm)
            self.pwm_right.ChangeDutyCycle(right_pwm)
            self.set_direction(
                self.left_forward_pin, self.left_backward_pin, left_speed >= 0.0
            )
            self.set_direction(
                self.right_forward_pin, self.right_backward_pin, right_speed >= 0.0
            )

        # debug topics used by oled / plots
        self.publish_debug(left_pwm, right_pwm, left_speed >= 0.0, right_speed >= 0.0)

    def speed_to_pwm(self, speed):
        pwm = (abs(speed) / self.max_speed) * self.max_pwm
        pwm = max(min(pwm, self.max_pwm), self.min_pwm)
        return pwm

    def set_direction(self, forward_pin, backward_pin, forward):
        if GPIO is None:
            return
        if forward:
            GPIO.output(forward_pin, GPIO.HIGH)
            GPIO.output(backward_pin, GPIO.LOW)
        else:
            GPIO.output(forward_pin, GPIO.LOW)
            GPIO.output(backward_pin, GPIO.HIGH)

    def stop_motors(self):
        if (
            self.backend == "gpio"
            and GPIO is not None
            and self.pwm_left
            and self.pwm_right
        ):
            self.pwm_left.ChangeDutyCycle(0)
            self.pwm_right.ChangeDutyCycle(0)
            GPIO.output(self.left_forward_pin, GPIO.HIGH)
            GPIO.output(self.left_backward_pin, GPIO.HIGH)
            GPIO.output(self.right_forward_pin, GPIO.HIGH)
            GPIO.output(self.right_backward_pin, GPIO.HIGH)
        self.publish_debug(0, 0, True, True)

    def publish_debug(self, left_pwm, right_pwm, left_forward, right_forward):
        lpwm = Int32()
        rpwm = Int32()
        ldir = Bool()
        rdir = Bool()
        lpwm.data = int(left_pwm)
        rpwm.data = int(right_pwm)
        ldir.data = left_forward
        rdir.data = right_forward
        self.publisher_lpwm.publish(lpwm)
        self.publisher_rpwm.publish(rpwm)
        self.publisher_ldir.publish(ldir)
        self.publisher_rdir.publish(rdir)

    def destroy_node(self):
        try:
            if self.context.ok():
                self.stop_motors()
        except Exception:
            pass
        if self.backend == "gpio" and GPIO is not None:
            with contextlib.suppress(Exception):
                GPIO.cleanup()
        super().destroy_node()


def main(args=None):
    # initialize ros, executor and node
    rclpy.init(args=args)
    node = DifferentialDriveNode()

    with contextlib.suppress(KeyboardInterrupt):
        rclpy.spin(node)

    # shutdown
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
