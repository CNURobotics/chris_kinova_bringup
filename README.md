chris_kinova_bringup
===================

This package launches nodes used in our lab setup with Kinova m1n6s200 robot arm.


This package is based on the https://github.com/kinovarobotics/kinova-ros.git ROS 1 code (BSD) and
https://github.com/hebirobotics ROS 2 code (Apache 2.0).

This package collects code from several packages to provide a single source for the
custom CHRISLab setup based on the m1n6s200 Kinova Mico arm.

The basic start up presumes a Hokoyu lidar and Realsense camera to provide 3D sensing inputs.
The lidar is not currently used in MoveIt as it would require adding conversion to 3D point cloud.

Planning and world modeling is provided by the MoveIt! 2 `move_group`, which includes the RViz visualization.

# Simulation

### Kinematic Visualization

A basic RViz view with fake joint state publishing is provided by:

* `ros2 launch chris_kinova_bringup view_model.launch.py`

### Kinematic Simulation Using Mock Hardware

* `clear; ros2 launch chris_kinova_bringup bringup_arm.launch.py`
  * `bringup_arm.launch.py` defaults to using `mock_hardware` and NOT launching `rviz`
* `clear; ros2 launch chris_kinova_bringup move_group.launch.py use_sim_time:=false`
  * For now, move_group defaults to `use_sim_time:=true` for Gazebo based testing

### Gazebo Physics-based Simulation

* `clear; ros2 launch chris_kinova_bringup bringup_arm_gazebo.launch.py`
* `clear; ros2 launch chris_kinova_bringup move_group.launch.py `

  > Note: Gazebo requires `move_group` use `use_sim_time:=true`, kinematic or actual hardware should not!


# Actual Hardware

The hardware driver is contained in the separate [`chris_kinova_driver`](https://github.com/CNURobotics/chris_kinova_driver) package.
See that README for instructions and cautions using the basic and experimental conversion of old ROS 1 code to use the ROS 2 controllers interface.


# Helper Scripts

A few simplified logging and plotting scripts are available

* `ros2 run chris_kinova_bringup kinova_controller_monitor`

  * This echo joint and controller status to terminal while also logging data to the `$WORKSPACE_ROOT/log/kinova_control` folder
  * `Ctrl-c` to terminate and close the log file.

* `ros2 run chris_kinova_bringup plot_kinova_controller_log`

  * This plots the last file saved by `plot_kinova_controller_log`

* `ros2 run chris_kinova_bringup live_plot_arm`
* `ros2 run chris_kinova_bringup live_plot_gripper`
  * These use a `bokeh server` to plot joint information in web browser window
  * Requires installation of `venv/bin/pip3 install bokeh`

* `ros2 run chris_kinova_bringup duckie`
  * Drops a yellow sphere (in lieu of rubber duck) into Gazebo world
  * fixed size and position for now


