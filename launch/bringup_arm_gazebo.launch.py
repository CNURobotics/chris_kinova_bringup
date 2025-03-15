# Copyright (c) 2024, Christopher Newport University
# Copyright (c) 2023, HEBI Robotics Inc.
# Copyright (c) 2022, Stogl Robotics Consulting UG (haftungsbeschränkt) (template)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, RegisterEventHandler, TimerAction, LogInfo, SetLaunchConfiguration, IncludeLaunchDescription
from launch.event_handlers import OnProcessExit, OnProcessStart
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution, PythonExpression, EqualsSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare

from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():
    # Declare arguments
    declared_arguments = []
    declared_arguments.append(
        DeclareLaunchArgument(
            "kinova_arm",
            default_value="m1n6s200",
            description="Name of the robot to be used.",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "description_package",
            default_value="chris_kinova_bringup",
            description="Description package with robot URDF/xacro files. Usually the argument \
        is not set, it enables use of a custom description.",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "description_file",
            default_value="None", # Default set later using the kinova arm name
            description="URDF/XACRO description file with the robot.",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "robot_controller",
            default_value="mico_arm_controller",
            choices=["mico_arm_controller"],
            description="Robot controller to start.",
        )
    )

    declared_arguments.append(
        DeclareLaunchArgument(
            "finger_controller",
            default_value="mico_finger_controller",
            choices=["mico_finger_controller"],
            description="Robot controller to start.",
        )
    )

    declared_arguments.append(
        DeclareLaunchArgument(
            "use_rviz",
            default_value="false",  # Presume we start with moveit
            description="Whether to start RViz.",
        )
    )

    # Set default values for arguments
    default_arguments = []
    default_arguments.append(
        LogInfo(
            msg=PythonExpression(['"Using arm: ', LaunchConfiguration("kinova_arm"), '"']),
        )
    )

    # Initialize Arguments
    description_package = LaunchConfiguration("description_package")
    robot_controller = LaunchConfiguration("robot_controller")
    finger_controller = LaunchConfiguration("finger_controller")

    # Get URDF via xacro
    robot_description_content = Command(
        [
            PathJoinSubstitution([FindExecutable(name="xacro")]),
            " ",
            PathJoinSubstitution(
            #    [FindPackageShare(description_package), "urdf", "sensors", "realsense_standalone.urdf.xacro"]  # include base frame
                [FindPackageShare(description_package), "urdf", "chris_kinova_lab.urdf.xacro"]  # include base frame
            #    [FindPackageShare(description_package), "urdf", "m1n6s200_standalone.urdf.xacro"]  # include base frame
            ),
            " ",
            "prefix:=m1n6s200 ",
            "use_mock_hardware:=false ",
            "mock_sensor_commands:=false ",
            "sim_gazebo:=true ",
            # "no_sensors:=true"  # Ignore the sensors and just launch arm if true
        ]
    )

    robot_description = {"robot_description": ParameterValue(robot_description_content, value_type=str)}

    rviz_config_file = PathJoinSubstitution(
        [FindPackageShare(description_package), "rviz", "kinova_arm.rviz"]
    )

    robot_state_pub_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="both",
        parameters=[robot_description, {"use_sim_time": True}],
    )
    rviz_node = Node(
        condition=IfCondition(LaunchConfiguration("use_rviz")),
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="log",
        arguments=["-d", rviz_config_file],
    )

    gz_bridge_node = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=[
            "/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock",
            "/camera/depth/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo",
            "/camera/depth/image@sensor_msgs/msg/Image[gz.msgs.Image",
            "/camera/depth/depth_image@sensor_msgs/msg/Image[gz.msgs.Image",
            "/camera/depth/points@sensor_msgs/msg/PointCloud2[gz.msgs.PointCloudPacked",
            "/hokuyo_node/scan_raw@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan",
            "/hokuyo_node/scan_raw/points@sensor_msgs/msg/PointCloud2[gz.msgs.PointCloudPacked",
       ],
        output="screen",
    )

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [PathJoinSubstitution([FindPackageShare('ros_gz_sim'), 'launch', 'gz_sim.launch.py'])]
        ),
        launch_arguments=[("gz_args", ["-r ", PathJoinSubstitution(
            [FindPackageShare(description_package), "config", "chrislab.sdf"]
        )])],
    )

    spawn_entity = Node(
        package="ros_gz_sim",
        executable="create",
        name="spawn_robot",
        arguments=["-topic",
                   "robot_description", # _gazebo_content,
                   "-name",
                   LaunchConfiguration("kinova_arm")],
        output="screen",
    )

    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster", "--controller-manager", "/controller_manager"],
    )

    robot_controller_names = [robot_controller, finger_controller]
    robot_controller_spawners = []
    for controller in robot_controller_names:
        robot_controller_spawners += [
            Node(
                package="controller_manager",
                executable="spawner",
                arguments=[controller, "-c", "/controller_manager"],
            )
        ]

    inactive_robot_controller_names = []
    inactive_robot_controller_spawners = []
    for controller in inactive_robot_controller_names:
        inactive_robot_controller_spawners += [
            Node(
                package="controller_manager",
                executable="spawner",
                arguments=[controller, "-c", "/controller_manager", "--inactive"],
            )
        ]

    # Delay loading and activation of `joint_state_broadcaster` after start of ros2_control_node
    delay_joint_state_broadcaster_spawner_after_ros2_control_node = RegisterEventHandler(
        event_handler=OnProcessStart(
            target_action=spawn_entity,
            on_start=[
                TimerAction(
                    period=5.0,
                    actions=[joint_state_broadcaster_spawner],
                ),
            ],
        )
    )

    # Delay loading and activation of robot_controller_names after `joint_state_broadcaster`
    delay_robot_controller_spawners_after_joint_state_broadcaster_spawner = []
    for i, controller in enumerate(robot_controller_spawners):
        delay_robot_controller_spawners_after_joint_state_broadcaster_spawner += [
            RegisterEventHandler(
                event_handler=OnProcessExit(
                    target_action=robot_controller_spawners[i - 1]
                    if i > 0
                    else joint_state_broadcaster_spawner,
                    on_exit=[controller],
                )
            )
        ]

    # Delay start of inactive_robot_controller_names after other controllers
    delay_inactive_robot_controller_spawners_after_joint_state_broadcaster_spawner = []
    for i, controller in enumerate(inactive_robot_controller_spawners):
        delay_inactive_robot_controller_spawners_after_joint_state_broadcaster_spawner += [
            RegisterEventHandler(
                event_handler=OnProcessExit(
                    target_action=inactive_robot_controller_spawners[i - 1]
                    if i > 0
                    else robot_controller_spawners[-1],
                    on_exit=[controller],
                )
            )
        ]

    return LaunchDescription(
        declared_arguments +
        default_arguments +
        [
            robot_state_pub_node,
            rviz_node,
            gazebo,
            spawn_entity,
            gz_bridge_node,
            delay_joint_state_broadcaster_spawner_after_ros2_control_node,  # joint_state_broadcaster_spawner,
        ]
        + delay_robot_controller_spawners_after_joint_state_broadcaster_spawner
        + delay_inactive_robot_controller_spawners_after_joint_state_broadcaster_spawner
    )
