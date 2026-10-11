#!/usr/bin/env python3
"""Simple Tk keyboard/button teleop that publishes geometry_msgs/Twist."""

import tkinter as tk
from tkinter import ttk

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node


class TwistPublisher(Node):
    def __init__(self):
        super().__init__('rviz_mecanum_teleop')
        self.publisher = self.create_publisher(Twist, '/cmd_vel', 10)

    def publish(self, vx=0.0, vy=0.0, wz=0.0):
        msg = Twist()
        msg.linear.x = float(vx)
        msg.linear.y = float(vy)
        msg.angular.z = float(wz)
        self.publisher.publish(msg)


class TeleopWindow:
    ACTIONS = {
        'forward': (1, 0, 0),
        'backward': (-1, 0, 0),
        'left': (0, 1, 0),
        'right': (0, -1, 0),
        'turn_left': (0, 0, 1),
        'turn_right': (0, 0, -1),
    }
    KEYS = {
        'w': 'forward', 's': 'backward', 'a': 'left', 'd': 'right',
        'q': 'turn_left', 'e': 'turn_right',
    }

    def __init__(self, node):
        self.node = node
        self.root = tk.Tk()
        self.root.title('Mecanum Robot Teleop - ROS 2 /cmd_vel')
        self.root.resizable(False, False)
        self.active = set()
        self.linear_speed = tk.DoubleVar(value=0.15)
        self.angular_speed = tk.DoubleVar(value=0.60)

        frame = ttk.Frame(self.root, padding=12)
        frame.grid(sticky='nsew')
        ttk.Label(frame, text='Hold a button or key to move; release to stop.').grid(
            row=0, column=0, columnspan=3, pady=(0, 8)
        )

        self._button(frame, 'Forward  [W]', 'forward', 1, 1)
        self._button(frame, 'Strafe left  [A]', 'left', 2, 0)
        self._button(frame, 'STOP', None, 2, 1, stop=True)
        self._button(frame, 'Strafe right  [D]', 'right', 2, 2)
        self._button(frame, 'Backward  [S]', 'backward', 3, 1)
        self._button(frame, 'Turn left  [Q]', 'turn_left', 4, 0)
        self._button(frame, 'Turn right  [E]', 'turn_right', 4, 2)

        ttk.Label(frame, text='Linear speed (m/s)').grid(
            row=5, column=0, columnspan=3, sticky='w', pady=(10, 0)
        )
        ttk.Scale(frame, from_=0.05, to=0.50, variable=self.linear_speed,
                  orient='horizontal').grid(row=6, column=0, columnspan=3, sticky='ew')
        ttk.Label(frame, text='Turn speed (rad/s)').grid(
            row=7, column=0, columnspan=3, sticky='w', pady=(8, 0)
        )
        ttk.Scale(frame, from_=0.10, to=2.00, variable=self.angular_speed,
                  orient='horizontal').grid(row=8, column=0, columnspan=3, sticky='ew')
        ttk.Label(frame, text='Publishes geometry_msgs/Twist on /cmd_vel').grid(
            row=9, column=0, columnspan=3, pady=(10, 0)
        )

        self.root.bind('<KeyPress>', self._key_press)
        self.root.bind('<KeyRelease>', self._key_release)
        self.root.protocol('WM_DELETE_WINDOW', self.close)
        self._publish_loop()

    def _button(self, parent, label, action, row, column, stop=False):
        button = ttk.Button(parent, text=label)
        button.grid(row=row, column=column, padx=3, pady=3, sticky='ew')
        if stop:
            button.configure(command=self.stop)
        elif action:
            button.bind('<ButtonPress-1>', lambda _event: self.active.add(action))
            button.bind('<ButtonRelease-1>', lambda _event: self.active.discard(action))

    def _key_press(self, event):
        key = event.keysym.lower()
        if key in self.KEYS:
            self.active.add(self.KEYS[key])
        elif key == 'space':
            self.stop()

    def _key_release(self, event):
        action = self.KEYS.get(event.keysym.lower())
        if action:
            self.active.discard(action)

    def _publish_loop(self):
        vx = vy = wz = 0.0
        for action in self.active:
            ax, ay, aw = self.ACTIONS[action]
            vx += ax
            vy += ay
            wz += aw
        # Clamp combined keyboard inputs so diagonals do not exceed slider limits.
        linear_scale = self.linear_speed.get() / max(1.0, abs(vx), abs(vy))
        angular_scale = self.angular_speed.get() / max(1.0, abs(wz))
        self.node.publish(vx * linear_scale, vy * linear_scale, wz * angular_scale)
        self.root.after(50, self._publish_loop)

    def stop(self):
        self.active.clear()
        self.node.publish()

    def close(self):
        self.stop()
        self.root.after(50, self.root.destroy)

    def run(self):
        self.root.mainloop()


def main(args=None):
    rclpy.init(args=args)
    node = TwistPublisher()
    try:
        TeleopWindow(node).run()
    finally:
        node.publish()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
