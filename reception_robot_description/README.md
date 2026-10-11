# reception_robot_description

ROS 2 Jazzy / Ubuntu 24.04 robot description and Gazebo Harmonic simulation for the pictured four wheel mecanum platform.

The photo does not give a scale. Every starting dimension below is an **estimate**, exposed as a Xacro argument. Replace these with measurements before using this model for fabrication, navigation calibration, or safety calculations.

## Model notes

Coordinates use X forward, Y left, Z up. base_footprint is at ground height and base_link is centered in the chassis plate. Wheels are at ±half wheelbase and ±half wheel separation. The X roller arrangement is FL/RR one slope and FR/RL the opposite slope. Wheel joint axes are local/robot Y.

Wheel collision is a cylinder; the eight angled rollers per wheel are visual details in the wheel link. Gazebo Harmonic's built in MecanumDrive system handles the four-wheel inverse kinematics and accepts body Twist commands. This gives forward, backward, strafe, diagonal, and yaw commands in simulation. The simplified roller collision does **not** resolve individual roller-ground contacts, so friction, impact, and slip are approximate. The simulation is useful for ROS command-path development, not a validated contact model.

The chassis, four motor envelopes, battery, ESP32, and L298N are represented with boxes and estimated inertias. The display mount is a configurable TF frame only; no screen mass or geometry is added yet.

### Estimated defaults

| Parameter | Default | Meaning |
|---|---:|---|
| chassis_length | 0.320 m | plate size along X |
| chassis_width | 0.280 m | plate size along Y |
| chassis_thickness | 0.012 m | plate thickness |
| wheel_radius | 0.035 m | 70 mm estimated outside diameter |
| wheel_width | 0.025 m | wheel axial width |
| wheelbase | 0.220 m | front/rear wheel center spacing |
| wheel_separation | 0.205 m | left/right wheel center spacing |
| motor_length, motor_width, motor_height | 0.070, 0.025, 0.025 m | motor envelope |
| battery_length, battery_width, battery_height | 0.105, 0.045, 0.025 m | two-cell pack envelope |
| display_mount_height | 0.350 m | frame height above base_link |

The component masses and inertias in the Xacro are also estimates; measure actual masses or replace them with CAD-derived values. The four wheels use 0.055 kg each, each yellow motor 0.080 kg, battery 0.180 kg, ESP32 0.015 kg, L298N board 0.035 kg, and chassis 1.20 kg.

To override dimensions when expanding the model, for example:

    ros2 run xacro xacro $(ros2 pkg prefix --share reception_robot_description)/urdf/reception_robot.urdf.xacro wheel_radius:=0.040 chassis_length:=0.36

## Install (Ubuntu 24.04 + ROS 2 Jazzy)

Install ROS 2 Jazzy first and source its setup file. Then install the ROS and Gazebo packages:

    sudo apt update
    sudo apt install ros-jazzy-xacro ros-jazzy-robot-state-publisher \
      ros-jazzy-joint-state-publisher-gui ros-jazzy-rviz2 \
      ros-jazzy-ros-gz ros-jazzy-teleop-twist-keyboard \
      ros-jazzy-urdf

ros-jazzy-ros-gz supplies the ROS/Gazebo bridge and Gazebo Sim integration for the Jazzy/Harmonic pairing. Do not install or load Gazebo Classic plugins for this package.

## Build

From the repository workspace root (the directory containing reception_robot_description/):

    source /opt/ros/jazzy/setup.bash
    colcon build --symlink-install
    source install/setup.bash

## View in RViz

    ros2 launch reception_robot_description display.launch.py

The joint state GUI is included so you can inspect wheel articulation. The display launch is for visualization; it does not simulate drive dynamics.

## Gazebo Harmonic

    ros2 launch reception_robot_description gazebo.launch.py

This launches the included flat world, spawns the robot, publishes robot_description and TF, and bridges ROS /cmd_vel to Gazebo's /model/reception_robot/cmd_vel. Joint states are bridged from Gazebo to ROS for wheel TF. The simulator's native mecanum system requires the gz-sim-mecanum-drive-system plugin supplied by Gazebo Sim Harmonic.

The launch and spawn were smoke-tested, and the ROS-to-Gazebo bridge initialized. A short forward command did not produce measurable wheel-joint rotation in the smoke test, so treat wheel motion as unresolved until you inspect the Gazebo mecanum plugin at runtime. Keyboard teleoperation (in another terminal after sourcing ROS and the workspace):

    ros2 run teleop_twist_keyboard teleop_twist_keyboard

The default topic is /cmd_vel. If the node prompts for a topic or uses a namespace, set it to /cmd_vel. Confirm the bridge receives messages with:

    ros2 topic echo /cmd_vel
    gz topic -e -t /model/reception_robot/cmd_vel

Stop with Ctrl-C. Keep the robot at low speeds when checking movement direction.

## URDF checks

After building and sourcing:

    xacro $(ros2 pkg prefix --share reception_robot_description)/urdf/reception_robot.urdf.xacro > /tmp/reception_robot.urdf
    check_urdf /tmp/reception_robot.urdf

check_urdf validates URDF structure, not Gazebo plugin loading or the realism of the contact model.

## Physical robot and ESP32 path

The shown single L298N is a dual H-bridge: it provides only **two independently controlled motor channels**. Four wheel mecanum motion requires independently setting speed and direction for all four motors. With one L298N, two motors must share each channel, so true four-wheel mecanum kinematics cannot be commanded. Add a second dual H-bridge (two drivers total, with current ratings suitable for motor stall current), or four suitable single-channel drivers. Then wire one channel per motor. This package includes example ESP32 firmware and a Wi-Fi UDP ROS 2 bridge for open-loop teleoperation; they do not add encoder feedback or a ros2_control hardware plugin. The Gazebo /cmd_vel bridge is separate and does not operate the physical robot. config/controllers.yaml remains a reference for a future ros2_control integration.

## Troubleshooting

- **Xacro or missing package:** source /opt/ros/jazzy/setup.bash and install/setup.bash, rebuild with colcon build --symlink-install, then rerun the launch.
- **No mesh appears:** the model intentionally uses primitive geometry and has no external mesh dependencies.
- **Wheel turns the wrong way:** verify the wheel is on the intended corner and check the MecanumDrive plugin joint names; check joint axis xyz="0 1 0". Roller visual slopes should be mirrored on FR/RL relative to FL/RR.
- **No /cmd_vel motion:** this model's drive response has not passed the wheel-rotation smoke test yet. Check teleop publishes /cmd_vel, confirm the bridge process is running, inspect /model/reception_robot/cmd_vel with gz topic -e, and check Gazebo output for MecanumDrive joint lookup or plugin errors. Also confirm nonzero velocity and effort limits on all four continuous wheel joints.
- **No wheel TF animation:** inspect /world/reception_world/model/reception_robot/joint_state; verify bridge startup and robot_state_publisher.
- **TF errors in RViz:** use base_footprint as Fixed Frame; check ros2 topic echo /tf and /tf_static, and confirm robot_state_publisher is running.
- **Spawn failure:** confirm gz sim -v 4 starts a world, wait for Gazebo to finish startup, and inspect whether ros_gz_sim create reports that robot_description was unavailable. Increase the spawn delay in launch/gazebo.launch.py if startup is slow.
- **Strafing/contact looks wrong:** visual rollers are not separate rolling collision bodies. This package uses the native MecanumDrive kinematics with approximate wheel friction; a roller-resolved physical model requires separate roller joints/contact geometry and careful solver tuning.

## Measurements needed for an accurate match

Please send the actual **chassis length, chassis width, wheel diameter, and wheel-center spacing** (front-to-rear and left-to-right if they differ). The photograph shows the overall layout, but it cannot establish these values.

## Real robot: ESP32 Wi-Fi and keyboard teleop

The physical control path is separate from Gazebo:

    teleop_twist_keyboard -> /cmd_vel -> wifi_mecanum_bridge -> Wi-Fi UDP -> ESP32 -> four H-bridge channels -> motors

This package includes the Arduino sketch at firmware/esp32_mecanum/esp32_mecanum.ino and a ROS 2 Python Wi-Fi bridge. The ESP32 joins your 2.4 GHz Wi-Fi network and listens for UDP commands on port 8888. The bridge sends four open-loop wheel speed targets in rad/s using mecanum inverse kinematics. The firmware converts targets to PWM and direction outputs and stops all motors if valid UDP commands stop for 500 ms. It does not read encoders or publish odometry. Consequently, keyboard teleop can drive the robot after the hardware is correctly wired, but this setup alone is not enough for reliable autonomous navigation or Nav2.

### Driver requirement before connecting motors

The photo shows one L298N, which has two independent H-bridge channels. The firmware and full mecanum command path require **four** independent channels, one per motor. Add a second dual-channel H-bridge with a current rating above the motor stall current, or use four suitable single-channel motor drivers. The example firmware assumes driver 1 runs FL/FR and driver 2 runs RL/RR. Do not connect all four motors to two channels and expect mecanum strafing or rotation.

Use a motor supply appropriate for the motor ratings and a regulated supply for the ESP32. Connect ESP32 ground to the motor-driver logic ground. Never power a motor from an ESP32 GPIO. Remove the L298N ENA/ENB jumpers for channels controlled by PWM. Check your exact driver board labels and motor current before wiring.

Example ESP32 GPIO mapping in the sketch (change it to match your build):

| Wheel | IN1 | IN2 | EN/PWM |
|---|---:|---:|---:|
| front-left | 16 | 17 | 18 |
| front-right | 19 | 21 | 22 |
| rear-left | 23 | 25 | 26 |
| rear-right | 27 | 32 | 33 |

Each row connects to one H-bridge channel. The sketch's per-motor invert flag corrects motor polarity; test and adjust it with wheels lifted. GPIO and PWM assignments are examples, not a verified wiring map for your particular driver boards.

### Flash the ESP32

1. Install Arduino IDE with Espressif's ESP32 Arduino core (version 2.x or 3.x).
2. Edit WIFI_SSID and WIFI_PASSWORD near the top of firmware/esp32_mecanum/esp32_mecanum.ino for your 2.4 GHz Wi-Fi network.
3. Open the sketch, select the ESP32 Dev Module board and the USB serial port, then upload.
4. Open Serial Monitor at 115200 baud and note the printed Robot Wi-Fi IP address. Use the serial cable only for flashing and diagnostics; motor commands travel over Wi-Fi. Keep the motor supply disconnected for the first firmware check.

### Run physical teleop

Make sure the ROS computer is on the same Wi-Fi network as the ESP32. Avoid guest Wi-Fi or client isolation, which can block device-to-device UDP. Install the keyboard teleop package once:

    sudo apt update
    sudo apt install ros-jazzy-teleop-twist-keyboard

Build/source the ROS package, then launch the **hardware** bridge (do not launch Gazebo for the physical robot). Replace 192.168.1.50 with the Robot Wi-Fi IP printed in Serial Monitor:

    cd /home/dhanush/Desktop/rosurdf
    source /opt/ros/jazzy/setup.bash
    colcon build --symlink-install
    source install/setup.bash
    ros2 launch reception_robot_description hardware.launch.py robot_ip:=192.168.1.50

If the router changes the ESP32 address, update robot_ip or configure a DHCP reservation in your router. In a second terminal, start keyboard teleop:

    source /opt/ros/jazzy/setup.bash
    source /home/dhanush/Desktop/rosurdf/install/setup.bash
    ros2 run teleop_twist_keyboard teleop_twist_keyboard

The bridge listens on /cmd_vel. Confirm the teleop messages with ros2 topic echo /cmd_vel. Test first with the robot supported so its wheels are clear of the ground. If a wheel spins opposite to the expected direction, change that motor's invert flag in the Arduino sketch, upload again, and retest at low speed.

Parameters can be overridden at launch. For example, set measured geometry and port:

    ros2 launch reception_robot_description hardware.launch.py robot_ip:=192.168.1.50 robot_port:=8888 wheel_radius:=0.040 wheelbase:=0.230 wheel_separation:=0.210

The bridge defaults match the current estimated Xacro dimensions. The ESP32 sketch and ROS bridge must use the same UDP port (8888 by default). Measure the real chassis and wheels before relying on distances or odometry. The pictured motors appear to have no encoders; add quadrature encoders to all four wheels and implement feedback before using wheel odometry or autonomous navigation. This initial bridge sends speed requests as open-loop PWM, not closed-loop RPM control.
