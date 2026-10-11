import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import ExecuteProcess, TimerAction
from launch.substitutions import Command, FindExecutable, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    share = get_package_share_directory('reception_robot_description')
    world = os.path.join(share, 'worlds', 'reception_world.sdf')
    xacro_file = PathJoinSubstitution(
        [FindPackageShare('reception_robot_description'), 'urdf', 'reception_robot.urdf.xacro']
    )
    robot_description = Command([FindExecutable(name='xacro'), ' ', xacro_file])
    gazebo = ExecuteProcess(
        cmd=['gz', 'sim', '-r', world],
        output='screen',
    )
    rsp = Node(package='robot_state_publisher', executable='robot_state_publisher',
               parameters=[{'robot_description': robot_description, 'use_sim_time': True}],
               output='screen')
    # Gazebo's Harmonic MecanumDrive consumes gz.msgs.Twist at this model topic.
    bridge = Node(package='ros_gz_bridge', executable='parameter_bridge',
                  arguments=['/model/reception_robot/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist',
                              '/world/reception_world/model/reception_robot/joint_state@sensor_msgs/msg/JointState[gz.msgs.Model'],
                  output='screen')
    spawn = TimerAction(period=3.0, actions=[
        Node(package='ros_gz_sim', executable='create',
             arguments=['-name', 'reception_robot', '-topic', 'robot_description',
                        '-x', '0', '-y', '0', '-z', '0'],
             output='screen')
    ])
    return LaunchDescription([gazebo, rsp, bridge, spawn])
