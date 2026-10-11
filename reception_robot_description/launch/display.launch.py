from launch import LaunchDescription
from launch.substitutions import Command, FindExecutable, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    xacro_file = PathJoinSubstitution(
        [FindPackageShare('reception_robot_description'), 'urdf', 'reception_robot.urdf.xacro']
    )
    robot_description = Command([FindExecutable(name='xacro'), ' ', xacro_file])
    return LaunchDescription([
        Node(package='robot_state_publisher', executable='robot_state_publisher',
             parameters=[{'robot_description': robot_description, 'use_sim_time': False}],
             output='screen'),
        Node(package='joint_state_publisher_gui', executable='joint_state_publisher_gui',
             parameters=[{'use_gui': True}], output='screen'),
        Node(package='rviz2', executable='rviz2',
             arguments=['-d', PathJoinSubstitution(
                 [FindPackageShare('reception_robot_description'), 'rviz', 'reception_robot.rviz'])],
             output='screen'),
    ])
