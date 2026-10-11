from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('robot_ip', default_value='192.168.1.50'),
        DeclareLaunchArgument('robot_port', default_value='8888'),
        DeclareLaunchArgument('wheel_radius', default_value='0.035'),
        DeclareLaunchArgument('wheelbase', default_value='0.220'),
        DeclareLaunchArgument('wheel_separation', default_value='0.205'),
        Node(
            package='reception_robot_description',
            executable='wifi_mecanum_bridge.py',
            name='wifi_mecanum_bridge',
            output='screen',
            parameters=[{
                'robot_ip': LaunchConfiguration('robot_ip'),
                'robot_port': LaunchConfiguration('robot_port'),
                'wheel_radius': LaunchConfiguration('wheel_radius'),
                'wheelbase': LaunchConfiguration('wheelbase'),
                'wheel_separation': LaunchConfiguration('wheel_separation'),
            }],
        ),
    ])
