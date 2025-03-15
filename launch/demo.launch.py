from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    # Declare launch arguments
    # db_arg = DeclareLaunchArgument(
    #     'db', default_value='false',
    #     description='By default, we do not start a database (it can be large)'
    # )

    # db_path_arg = DeclareLaunchArgument(
    #     'db_path', default_value=[FindPackageShare('m1n6s200_moveit_config'), '/default_warehouse_mongo_db'],
    #     description='Allow user to specify database location'
    # )

    debug_arg = DeclareLaunchArgument(
        'debug', default_value='false',
        description='By default, we are not in debug mode'
    )

    # Find package share directory
    moveit_config_share = FindPackageShare(package='chris_kinova_bringup').find('chris_kinova_bringup')

    # Include planning_context.launch
    planning_context_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([moveit_config_share, '/launch/planning_context.launch.py']),
        launch_arguments={'load_robot_description': 'true'}.items()
    )

    # Node: joint_state_publisher
    joint_state_publisher_node = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        name='joint_state_publisher',
        parameters=[{'use_gui': False}],
        remappings=[('/source_list', ['/move_group/fake_controller_joint_states'])]
    )

    # Node: robot_state_publisher
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        respawn=True
    )

    # Include move_group.launch.py
    move_group_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([moveit_config_share, '/launch/move_group.launch.py']),
        launch_arguments={
            'allow_trajectory_execution': 'true',
            'fake_execution': 'true',
            'info': 'true',
            'debug': LaunchConfiguration('debug')
        }.items()
    )

    # Include moveit_rviz.launch.py
    moveit_rviz_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([moveit_config_share, '/launch/moveit_rviz.launch.py']),
        launch_arguments={
            'config': 'true',
            'debug': LaunchConfiguration('debug')
        }.items()
    )

    # Include default_warehouse_db.launch.py conditionally
    # default_warehouse_db_launch = IncludeLaunchDescription(
    #     PythonLaunchDescriptionSource([moveit_config_share, '/launch/default_warehouse_db.launch.py']), #TODO- Have not created yet!
    #     condition=IfCondition(LaunchConfiguration('db')),
    #     launch_arguments={'moveit_warehouse_database_path': LaunchConfiguration('db_path')}.items()
    # )

    # Return LaunchDescription
    return LaunchDescription([
        # db_arg,
        # db_path_arg,
        debug_arg,
        planning_context_launch,
        #joint_state_publisher_node,
        #robot_state_publisher_node,
        #move_group_launch,
        #moveit_rviz_launch,
        #default_warehouse_db_launch
    ])