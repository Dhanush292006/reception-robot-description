#!/usr/bin/env python3
"""Bridge ROS Twist commands to an ESP32 mecanum controller over Wi-Fi UDP."""

import socket
import time

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node


class WifiMecanumBridge(Node):
    def __init__(self):
        super().__init__('wifi_mecanum_bridge')
        self.declare_parameter('robot_ip', '192.168.1.50')
        self.declare_parameter('robot_port', 8888)
        self.declare_parameter('wheel_radius', 0.035)
        self.declare_parameter('wheelbase', 0.220)
        self.declare_parameter('wheel_separation', 0.205)
        self.declare_parameter('max_wheel_speed', 20.0)
        self.declare_parameter('command_timeout', 0.5)
        self.declare_parameter('publish_rate', 20.0)
        self.declare_parameter('wheel_signs', [1.0, 1.0, 1.0, 1.0])

        self.robot_ip = str(self.get_parameter('robot_ip').value)
        self.robot_port = int(self.get_parameter('robot_port').value)
        self.radius = float(self.get_parameter('wheel_radius').value)
        self.wheelbase = float(self.get_parameter('wheelbase').value)
        self.separation = float(self.get_parameter('wheel_separation').value)
        self.max_speed = float(self.get_parameter('max_wheel_speed').value)
        self.timeout = float(self.get_parameter('command_timeout').value)
        self.wheel_signs = [float(v) for v in self.get_parameter('wheel_signs').value]
        if self.radius <= 0.0 or self.max_speed <= 0.0 or len(self.wheel_signs) != 4:
            raise ValueError('wheel_radius/max_wheel_speed must be positive and wheel_signs must have 4 values')

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.robot_address = (self.robot_ip, self.robot_port)
        self.latest = [0.0, 0.0, 0.0, 0.0]
        self.last_command_time = time.monotonic()
        self.sequence = 0
        self.subscription = self.create_subscription(Twist, '/cmd_vel', self.on_cmd_vel, 10)
        rate = max(1.0, float(self.get_parameter('publish_rate').value))
        self.timer = self.create_timer(1.0 / rate, self.send_wheel_speeds)
        self.get_logger().info(f'Wi-Fi UDP bridge sending to {self.robot_ip}:{self.robot_port}; subscribing to /cmd_vel')

    def on_cmd_vel(self, msg: Twist):
        vx = float(msg.linear.x)
        vy = float(msg.linear.y)
        wz = float(msg.angular.z)
        arm = 0.5 * (self.wheelbase + self.separation)
        r = self.radius
        # Order: front-left, front-right, rear-left, rear-right.
        speeds = [
            (vx - vy - arm * wz) / r,
            (vx + vy + arm * wz) / r,
            (vx + vy - arm * wz) / r,
            (vx - vy + arm * wz) / r,
        ]
        peak = max(abs(v) for v in speeds)
        if peak > self.max_speed:
            scale = self.max_speed / peak
            speeds = [v * scale for v in speeds]
        self.latest = [v * sign for v, sign in zip(speeds, self.wheel_signs)]
        self.last_command_time = time.monotonic()

    def send_wheel_speeds(self):
        if time.monotonic() - self.last_command_time > self.timeout:
            speeds = [0.0, 0.0, 0.0, 0.0]
        else:
            speeds = self.latest
        self.sequence = (self.sequence + 1) % 2_000_000_000
        packet = 'CMD,{},{:.4f},{:.4f},{:.4f},{:.4f}'.format(self.sequence, *speeds)
        try:
            self.socket.sendto(packet.encode('ascii'), self.robot_address)
        except OSError as exc:
            self.get_logger().error(f'UDP send failed; ESP32 watchdog should stop the motors: {exc}')
            self.latest = [0.0, 0.0, 0.0, 0.0]

    def destroy_node(self):
        try:
            for _ in range(3):
                self.socket.sendto(b'CMD,0,0,0,0,0', self.robot_address)
                time.sleep(0.02)
            self.socket.close()
        except (OSError, AttributeError):
            pass
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = None
    try:
        node = WifiMecanumBridge()
        rclpy.spin(node)
    except (OSError, ValueError) as exc:
        print(f'Could not start mecanum Wi-Fi bridge: {exc}')
        raise SystemExit(1)
    except KeyboardInterrupt:
        pass
    finally:
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
