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
from launch_ros.actions import Node


def generate_launch_description():

    rviz_config_dir = os.path.join(get_package_share_directory('chris_kinova_bringup'), 'config', 'model_view.rviz')
    xacro_path = os.path.join(get_package_share_directory('chris_kinova_bringup'), 'urdf', 'chris_kinova_lab.urdf.xacro')
    print(f"xacro path = '{xacro_path}'")

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_config_dir],
        parameters=[{'use_sim_time': False}]
        )


    return launch.LaunchDescription([rviz_node])
