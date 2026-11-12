#!/usr/bin/env python3
"""Publish /cmd_vel_key Twist from keyboard keys for teleoperation."""

import sys
import termios
import tty

import rclpy
from geometry_msgs.msg import Twist

MSG = """
This node takes keypresses from the keyboard and publishes them
as Twist messages. It works best with a US keyboard layout.
---------------------------
Moving around:
   u    i    o
   j    k    l
   m    ,    .
anything else : stop
q/z : increase/decrease max speeds by 10%
w/x : increase/decrease only linear speed by 10%
e/c : increase/decrease only angular speed by 10%
CTRL-C to quit
"""

MOVE_BINDINGS = {
    "i": (1, 0, 0, 0),
    "o": (1, 0, 0, -1),
    "j": (0, 0, 0, 1),
    "l": (0, 0, 0, -1),
    "u": (1, 0, 0, 1),
    ",": (-1, 0, 0, 0),
    ".": (-1, 0, 0, 1),
    "m": (-1, 0, 0, -1),
}

SPEED_BINDINGS = {
    "q": (1.1, 1.1),
    "z": (0.9, 0.9),
    "w": (1.1, 1.0),
    "x": (0.9, 1.0),
    "e": (1.0, 1.1),
    "c": (1.0, 0.9),
}


def get_key(settings):
    tty.setraw(sys.stdin.fileno())
    key = sys.stdin.read(1)
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
    return key


def format_vels(speed, turn):
    return f"currently:\tspeed {speed}\tturn {turn} "


def main(args=None):
    # initialize ros, executor and node
    settings = termios.tcgetattr(sys.stdin)
    rclpy.init(args=args)
    node = rclpy.create_node("teleop_twist_keyboard")
    publisher_cmd = node.create_publisher(Twist, "/cmd_vel_key", 10)

    # real robot motors top out near 0.20 m/s
    speed = 0.20
    turn = 1.0
    x = 0.0
    th = 0.0

    try:
        print(MSG)
        print(format_vels(speed, turn))
        while True:
            key = get_key(settings)
            if key in MOVE_BINDINGS:
                x = MOVE_BINDINGS[key][0]
                th = MOVE_BINDINGS[key][3]
            elif key in SPEED_BINDINGS:
                speed = speed * SPEED_BINDINGS[key][0]
                turn = turn * SPEED_BINDINGS[key][1]
                print(format_vels(speed, turn))
            else:
                x = 0.0
                th = 0.0
                if key == "\x03":
                    break

            message = Twist()
            message.linear.x = x * speed
            message.angular.z = th * turn
            publisher_cmd.publish(message)
    except Exception as exc:
        print(exc)
    finally:
        # publish zero on exit
        message = Twist()
        publisher_cmd.publish(message)
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
        # shutdown
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
