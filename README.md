chris_kinova_bringup
===================

This package launches nodes used in our lab setup with Kinova m1n6s200 robot arm.
The bringup make some adjustments to the default Kinova topic names.


This package includes options for bringing the robot arm standalone as ```kinova```, or
in our lab configuration with a Hokuyo Lidar and Kinect sensor as ```kinova_lab```.

# Startup instructions

First start a ```roscore``` node on the designated machine, with networking configured
appropriately.

## Simulation
First launch the base Gazebo simulatin framework.
```
roscore
roslaunch gazebo_ros empty_world.launch
```
You may replace the ```empty_world``` with any desired Gazebo world file.

Then choose the appropriate hardware simulation.

1. For a stand alone robot arm, use:

```
roslaunch chris_kinova_bringup chris_kinova_robot_gazebo.launch
```

2. For our lab configuration with the single robot arm, Hokuyo lidar,
and Kinect sensor use:

```
roslaunch chris_kinova_bringup chris_kinova_lab_gazebo.launch
```

Only use one of the ```_gazebo.launch``` files.

## hardware

To launch the equivalent nodes in the robot hardware, use either:

1. Standalone arm

```
roslaunch chris_kinova_bringup chris_kinova_robot_hardware.launch
```

2. Lab setup with a single robot arm and Kinect and Hokuyo LIDAR sensors

```
roslaunch chris_kinova_bringup chris_kinova_lab_hardware.launch
```

Then run
```
rosrun  kinova_driver  joint_trajectory_action_server m1n6s200
```
to start the controller interfaces for either setup.

## Arm Controllers

With either simulation or hardware, run

```
roslaunch chris_kinova_bringup chris_kinova_controllers.launch
```

## MoveIt Planning Software

With either simulation or hardware, run
```
roslaunch chris_kinova_bringup chris_moveit_demo.launch
```
which starts the MoveIt! planning system.
This launch includes the RViz visualization with
MoveIt! control plugin.

## Optional visualization (without MoveIt! Control plugin)

A basic RViz view is provided by:
```
roslaunch chris_kinova_bringup chris_kinova_rviz.launch
```
