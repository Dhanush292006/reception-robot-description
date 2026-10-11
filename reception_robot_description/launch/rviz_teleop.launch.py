from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    display_launch = PathJoinSubstitution([
        FindPackageShare('reception_robot_description'), 'launch', 'display.launch.py'
    ])
    return LaunchDescription([
        IncludeLaunchDescription(PythonLaunchDescriptionSource(display_launch)),
        Node(
            package='reception_robot_description',
            executable='rviz_mecanum_teleop.py',
            name='rviz_mecanum_teleop',
            output='screen',
        ),
    ])
