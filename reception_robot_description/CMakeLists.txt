cmake_minimum_required(VERSION 3.8)
project(reception_robot_description)
find_package(ament_cmake REQUIRED)
install(DIRECTORY urdf meshes config launch worlds rviz firmware
  DESTINATION share/${PROJECT_NAME})
install(PROGRAMS
  scripts/wifi_mecanum_bridge.py
  scripts/rviz_mecanum_teleop.py
  DESTINATION lib/${PROJECT_NAME})
ament_package()
