# Copyright 2025 Christopher Newport University
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

import os

from ament_index_python.packages import get_package_share_directory
import launch
import launch.events
from launch_ros.actions import Node
import xacro
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition
import os


def generate_launch_description():
    urdf_file = os.path.join(get_package_share_directory('chris_kinova_bringup'), 'urdf', 'chris_kinova_lab.urdf.xacro')
    print(f"xacro path = '{urdf_file}'")
    robot_description = xacro.process_file(urdf_file, mappings={'use_nominal_extrinsics': 'true', 'add_plug': 'true'}).toprettyxml(indent='  ')


    return LaunchDescription([
        DeclareLaunchArgument(
            'gui', default_value='true', description='Flag to enable joint_state_publisher_gui'
        ),

        Node(
            package='joint_state_publisher_gui',
            executable='joint_state_publisher_gui',
            condition=IfCondition(LaunchConfiguration('gui')),
            name='joint_state_publisher'
        ),

        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            parameters=[{'robot_description': robot_description}]
        ),

        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            output='screen',
            arguments=['-d', os.path.join(
                get_package_share_directory('chris_kinova_bringup'),
                'config',
                'model_view.rviz'  # optional, or leave this line out for default view
            )]
        ),
    ])
