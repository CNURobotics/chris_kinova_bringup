from pathlib import Path

from moveit_configs_utils import MoveItConfigsBuilder
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction, LogInfo, SetEnvironmentVariable, SetLaunchConfiguration
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, PythonExpression, EqualsSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

from launch.conditions import IfCondition


def generate_moveit_nodes(context, *args, **kwargs):
    # Resolve kinova_arm configuration during runtime
    kinova_arm_urdf = LaunchConfiguration("kinova_arm_urdf").perform(context)
    kinova_arm_name = LaunchConfiguration("kinova_arm_name").perform(context)
    moveit_package = "chris_kinova_bringup"  # MoveIt configs for CNU setup

    # Initialize Arguments
    description_package = LaunchConfiguration("description_package")
    description_file = LaunchConfiguration("description_file")

    description_filepath = PathJoinSubstitution(
        [FindPackageShare(description_package), "urdf",  description_file]
    ).perform(context)

    if '_MoveItConfigsBuilder__config_dir_path' in MoveItConfigsBuilder.__dict__:
        print("Setting custom MoveIt config directory for chris_kinova_bringup setup ...")
        setattr(MoveItConfigsBuilder, '_MoveItConfigsBuilder__config_dir_path', Path("config/moveit"))
        print(f"    using custom '{MoveItConfigsBuilder._MoveItConfigsBuilder__config_dir_path}' path!")
    else:
        print("Cannot set Config builder custom path!")
        print(MoveItConfigsBuilder.__dict__)
        raise Exception("Cannot set custom MoveIt config for chris_kinova_bringup setup !")

    moveit_config = MoveItConfigsBuilder(
        robot_name=kinova_arm_urdf,
        package_name=moveit_package,
    ).robot_description(
        description_filepath
    ).to_moveit_configs()

    # print(30*'=')
    # print(30*'=')
    # for key, val in moveit_config.to_dict().items():
    #     if "robot_desc" not in key:
    #         print(f'{key:20s} -> {val}\n')
    #     else:
    #         # if "realsense" in val:
    #         #     print("Realsense!")
    #         # else:
    #         print(f'{key:20s} -> {val}\n')

    #     print(30*'-')
    # print(30*'=')
    # print(30*'=')

    return [
        SetEnvironmentVariable('RCL_LOG_LEVEL', 'moveit_planners_ompl.debug'),

        Node(
            package="moveit_ros_move_group",
            executable="move_group",
            output="screen",
            parameters=[
                moveit_config.to_dict(),
                {'use_sim_time': LaunchConfiguration("use_sim_time")},
            ],
            arguments=["--ros-args", "--log-level",   "info"],  #  "move_group:=debug"],  #
            remappings=[('/joint_states', f'/{kinova_arm_name}/joint_states')]

        ),
        Node(
            package="rviz2",
            executable="rviz2",
            arguments=["-d", str(moveit_config.package_path / "config/moveit/moveit.rviz")],
            output="screen",
            parameters=[
                moveit_config.robot_description,
                moveit_config.robot_description_semantic,
                moveit_config.planning_pipelines,
                moveit_config.robot_description_kinematics,
                moveit_config.joint_limits,
                {'use_sim_time': LaunchConfiguration("use_sim_time")},
            ],
        )
    ]

def generate_launch_description():
    # Declare arguments
    declared_arguments = []
    declared_arguments.append(
        DeclareLaunchArgument(
            "kinova_arm_name",
            default_value="m1n6s200",
            description="Name of the robot to be used.",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "kinova_arm_urdf",
            default_value="chris_kinova_lab", # "m1n6s200",
            description="Name of the robot urdf file.",
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
            "use_sim_time",
            default_value="true",
            description="Use simulation (Gazebo) clock if true.",
        )
    )

    # Set default values for arguments
    default_arguments = []
    default_arguments.append(
        LogInfo(
            msg=PythonExpression(['"Using default description_file: ', LaunchConfiguration("kinova_arm_urdf"), '.urdf.xacro"']),
            condition=IfCondition(
                EqualsSubstitution(LaunchConfiguration('description_file'), "None")
            )
        )
    )
    default_arguments.append(
        SetLaunchConfiguration(
            name="description_file",
            value=PythonExpression(['"', LaunchConfiguration("kinova_arm_urdf"), '.urdf.xacro"']),
            condition=IfCondition(
                EqualsSubstitution(LaunchConfiguration('description_file'), "None")
            )
        )
    )
    default_arguments.append(
        LogInfo(
            msg=PythonExpression(['"Using use_sim_time=', LaunchConfiguration("use_sim_time"), '"']),
        )
    )

    return LaunchDescription(
        declared_arguments +
        default_arguments +
        [
            OpaqueFunction(function=generate_moveit_nodes)
        ]
    )

