cmake_minimum_required(VERSION 3.5)
project(chris_kinova_bringup)

find_package(ament_cmake REQUIRED)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

install(DIRECTORY config launch meshes urdf
        DESTINATION share/${PROJECT_NAME}
)

install(PROGRAMS
  scripts/duckie
  scripts/kinova_controller_monitor
  scripts/live_gripper.py
  scripts/live_plot_arm
  scripts/live_plot_gripper
  scripts/live_plot.py
  scripts/plot_kinova_controller_log
  DESTINATION lib/${PROJECT_NAME}
)
ament_package()

