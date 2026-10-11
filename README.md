# Wi-Fi Mecanum Robot (ROS 2 Jazzy)

ROS 2 description, Gazebo Harmonic simulation, and Wi-Fi keyboard teleoperation for a four-wheel mecanum robot based on the photographed build.

## Quick start: simulation

On Ubuntu 24.04 with ROS 2 Jazzy and Gazebo Harmonic installed:

Run these commands from the root of a clone of this repository:

```bash
sudo apt install ros-jazzy-xacro ros-jazzy-robot-state-publisher \
  ros-jazzy-joint-state-publisher-gui ros-jazzy-rviz2 \
  ros-jazzy-ros-gz ros-jazzy-teleop-twist-keyboard ros-jazzy-urdf python3-tk
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
source install/setup.bash
ros2 launch reception_robot_description gazebo.launch.py
```

In another terminal, source ROS and the workspace, then run:

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

## Physical robot: Wi-Fi teleoperation

The control path is `teleop_twist_keyboard -> /cmd_vel -> ROS UDP bridge -> Wi-Fi -> ESP32 -> motor drivers`.

1. Flash `reception_robot_description/firmware/esp32_mecanum/esp32_mecanum.ino` after setting the 2.4 GHz Wi-Fi name and password in the sketch. Note the ESP32 IP printed in Serial Monitor.
2. The pictured single L298N has only two motor channels. Add a second suitable dual H-bridge (four independently controlled channels total), wire one channel per wheel, and check driver current ratings against motor stall current. Test with wheels lifted and low speeds first.
3. Build and launch the Wi-Fi bridge on a ROS 2 computer on the same non-isolated network:

   ```bash
   source /opt/ros/jazzy/setup.bash
   colcon build --symlink-install
   source install/setup.bash
   ros2 launch reception_robot_description hardware.launch.py robot_ip:=ESP32_IP
   ```

4. In another terminal, source ROS and the workspace, then run `ros2 run teleop_twist_keyboard teleop_twist_keyboard`. The bridge converts `/cmd_vel` into mecanum wheel speeds and sends them over UDP port 8888. The ESP32 stops the motors if commands stop arriving.

This is open-loop PWM control: the example does not read encoders or provide odometry. It is not ready for autonomous navigation. GPIO mappings, wheel geometry, motor direction, and driver wiring must be checked against the actual robot. Keep the robot supported during first tests.

## Python GUI teleop with RViz

For an RViz view with a Python control window, run:

```bash
ros2 launch reception_robot_description rviz_teleop.launch.py
```

The GUI has hold-to-move buttons, WASD translation, Q/E rotation, speed sliders, and a stop button. It publishes `/cmd_vel`. For the real robot, run `hardware.launch.py` in another sourced terminal with the ESP32 IP. For Gazebo, start `gazebo.launch.py` and run `ros2 run reception_robot_description rviz_mecanum_teleop.py` in another terminal; the GUI publishes to the same simulation `/cmd_vel` path.

## Full instructions

See [`reception_robot_description/README.md`](reception_robot_description/README.md) for installation, model dimensions, detailed wiring and flashing steps, launch options, troubleshooting, and simulation limitations.
