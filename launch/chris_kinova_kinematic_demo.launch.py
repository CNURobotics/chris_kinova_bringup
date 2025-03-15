from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():
    # Find the share directory of the m1n6s200_moveit_config package
    moveit_config_share = get_package_share_directory('chris_kinova_bringup')

    # Construct the path to the demo.launch.py file
    demo_launch_file = moveit_config_share + '/launch/demo.launch.py'

    # Include the demo launch file
    demo_launch_include = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(demo_launch_file)
    )

    # Return the launch description
    return LaunchDescription([demo_launch_include])