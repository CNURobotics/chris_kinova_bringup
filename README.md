chris_kinova_bringup
===================

This package launches nodes used in our lab setup with Kinova m1n6s200 robot arm.


This package depends on the modified ``cnu_mico`` branch of ``kinova-ros`` as it
makes some adjustments to the default Kinova topic names.


This package includes options for bringing the robot arm standalone as ```kinova_robot```, or
in our lab configuration with a Hokuyo Lidar and Kinect sensor as ```kinova_lab```.


# Startup instructions

First start a ```roscore``` node on the designated machine, with networking configured
appropriately.

## Simulation
Launch the base Gazebo simulation environment:
```
roslaunch gazebo_ros empty_world.launch
```
We start Gazebo separately to allow easier configuration of world workspace models.
You may replace the ```empty_world``` with any desired Gazebo world file.

Then choose the appropriate device simulation.

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
The lab set up includes transformations between the sensors and the robot.

For either hardware setup run,
```
rosrun  kinova_driver  joint_trajectory_action_server m1n6s200
```
to start the controller interfaces.
This starts up the ....<Later>.

## Arm Controllers

With either simulation or hardware, choose either:

1. Trajectory controllers (that interface with MoveIt!)

```
roslaunch chris_kinova_bringup chris_kinova_trajectory_controllers.launch
```

or

2. Individual joint controllers

```
roslaunch chris_kinova_bringup chris_kinova_joint_controllers.launch
```

Starting both will result in a resource conflict, unless you modify the ``start_controllers`` parameter to ``--stopped``.



## MoveIt Planning Software

With either simulation or hardware, run
```
roslaunch chris_kinova_bringup chris_moveit_demo.launch
```
which starts the MoveIt! planning system which interfaces with the trajectory controllers.

This launch includes the RViz visualization with
MoveIt! control plugin.

## Optional visualization (without MoveIt! Control plugin)

A basic RViz view is provided by:
```
roslaunch chris_kinova_bringup chris_kinova_rviz.launch
```
