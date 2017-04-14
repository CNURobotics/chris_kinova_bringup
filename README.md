chris_kinova_bringup
===================

This package launches nodes used in our lab setup with Kinova m1n6s200 robot arm.


To run the typical configuration with the single robot arm, hokuyo lidar, and kinect sensor in simulation:
```
roscore
roslaunch gazebo_ros empty_world.launch
roslaunch chris_kinova_bringup chris_kinova_gazebo.launch
roslaunch chris_kinova_bringup chris_kinova_rviz.launch

```
Replace empty_world by the desired world model.

To bring up the equivalent setup on hardware:
```
roscore
roslaunch chris_kinova_bringup chris_kinova_bringup.launch
roslaunch chris_kinova_bringup chris_kinova_rviz.launch

```
