import os
from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, LogInfo
from launch.substitutions import Command,LaunchConfiguration, PathJoinSubstitution
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.actions import Node

import xacro

def generate_launch_description():

    bringup_description_dir = get_package_share_directory('chris_kinova_bringup')
    bringup_config_dir = get_package_share_directory('chris_kinova_bringup')

    # Declare launch arguments.

    # By default we do not overwrite the URDF. Change the following to true to change the default behavior.
    load_robot_description_arg = DeclareLaunchArgument(
        'load_robot_description',
        default_value='false'
    )

    # The name of the parameter under which the URDF is loaded
    robot_description_arg = DeclareLaunchArgument(
        'robot_description',
        default_value='robot_description'
    )

    # Load universal robot description format (URDF)
    urdf_file = os.path.join(
       bringup_description_dir,
       'urdf',
       'm1n6s200_standalone.urdf.xacro'
    )

    print(f'urdf file = ${urdf_file}')



    # robot_description_xacro = Command(['xacro ', urdf_file])
    # # Declare launch arguments
    # declare_robot_description = DeclareLaunchArgument(
    #     'robot_description',
    #     default_value=robot_description_xacro,
    #     description='Robot URDF description'
    # )
    # log_debug_desc_info = LogInfo(
    #     msg=[
    #         'Debug: URDF: ', LaunchConfiguration('declare_robot_description')
    #     ]
    # )


    # Load semantic description that corresponds to the URDF
    semantic_file = os.path.join(
        bringup_config_dir,
        'config',
        'moveit',
        'm1n6s200.srdf'
    )
    with open(semantic_file, 'r') as f:
        semantic_content = f.read()

    # Loading the robot description file
    doc = xacro.parse(open(urdf_file))
    xacro.process_doc(doc)
    params = {'robot_description': doc.toxml()}

    # Load updated joint limits (override information from URDF)
    joint_limits_file = os.path.join(
        bringup_config_dir,
        'config',
        'joint_limits.yaml'
    )

    # Load default settings for kinematics; these settings are overridden by settings in a node's namespace
    kinematics_file = os.path.join(
        bringup_config_dir,
        'config',
        'kinematics.yaml'
    )

    print("Setting up move_group node ...")
    move_group_node = Node(
        package='moveit_ros_move_group',
        executable='move_group',
        name="move_group",
        output='screen',
        parameters=[{
            'robot_description': params['robot_description'],
            'robot_description_semantic': semantic_content,
            # Other necessary parameters
            "planning_plugin": "ompl_interface/OMPLPlanner",
            "pipeline_id": "ompl",  # Match this with your planner type
        }]
    )

    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': params['robot_description'],
            'publish_frequency': 15.0
        }]
    )

    # load_joint_limits = ExecuteProcess(
    #     cmd=['ros2', 'param', 'load', joint_limits_file],
    #     output='screen'
    # )

    # load_kinematics = ExecuteProcess(
    #     cmd=['ros2', 'param', 'load', kinematics_file],
    #     output='screen'
    # )

    ld = LaunchDescription()
    #ld.add_action(urdf_file)
    #ld.add_action(load_robot_description_arg)
    #ld.add_action(robot_description_arg)
    #ld.add_action(declare_robot_description)
    #ld.add_action(log_debug_desc_info)
    ld.add_action(robot_state_publisher_node)
    ld.add_action(move_group_node)
    #ld.add_action(load_joint_limits)
    #ld.add_action(load_kinematics)

    return ld
