================================================================================
third_party — WHAT WE MODIFIED
================================================================================
This folder is not original TortoiseBot code. A bug in here is not ours
to fix by instinct. ROS package names stay upstream (ydlidar_*,
cartographer*).

Edits exist only so these packages compile and run on ROS 2 Lyrical.
We do not rewrite their algorithms. Do not restyle vendor C++.
Remove these trees once the original packages work on Lyrical or have
been migrated.

If a file is not in this list, treat it as untouched upstream.
When you change a vendor file, add a line here — not a comment in the
source.

Rebuild after an edit:   colcon build --symlink-install
Install ROS deps:        rosdep install --from-paths . --ignore-src -y --skip-keys ament_python
Check they are visible:  ros2 pkg list | grep -E 'cartographer|ydlidar'

Warnings are suppressed on purpose (CMake -w in vendor trees; fleet's
colcon.meta adds -Wno-dev). Our tortoisebot_* packages still compile
with normal warnings.


--------------------------------------------------------------------------------
PACKAGE LIST
--------------------------------------------------------------------------------
    ydlidar_sdk              cmake library     ydlidar_sdk/
    ydlidar_ros2_driver      ament_cmake       ydlidar_ros2_driver/
    cartographer             cmake library     cartographer/
    cartographer_ros         ament_cmake       cartographer_ros/cartographer_ros/

--------------------------------------------------------------------------------
PINNED UPSTREAM (this file only; no nested .git)
--------------------------------------------------------------------------------
    ydlidar_sdk
        https://github.com/YDLIDAR/YDLidar-SDK
        version 1.2.6     vendored 2026-09-07

    ydlidar_ros2_driver
        https://github.com/YDLIDAR/ydlidar_ros2_driver  branch humble
        version 1.0.1     vendored 2026-09-07

    cartographer
        https://github.com/ros2/cartographer.git  branch ros2
        1489fc933b6e0b1da936ca08af462abe559dd02e
        tag 2.0.9004      vendored 2026-09-07

    cartographer_ros
        https://github.com/ros2/cartographer_ros.git  branch ros2
        743345256b43a7fd95765d40c7332b6f31ab66bb
        version 2.0.9003  vendored 2026-09-07

Used from apt, not vendored
    cartographer_ros_msgs    ros-lyrical-cartographer-ros-msgs

Not built (ignored)
    cartographer_ros_msgs    cartographer_ros/cartographer_ros_msgs/COLCON_IGNORE
    cartographer_rviz        cartographer_ros/cartographer_rviz/COLCON_IGNORE


================================================================================
QUICK TABLE
================================================================================
Package                 File                                         Kind
----------------------  -------------------------------------------  ------
ydlidar_sdk             package.xml                                  ADDED
ydlidar_sdk             CMakeLists.txt                               EDIT
ydlidar_sdk             core/CMakeLists.txt                          EDIT
ydlidar_sdk             examples/CMakeLists.txt                      EDIT
ydlidar_sdk             cmake/install_package.cmake                  EDIT

ydlidar_ros2_driver     CMakeLists.txt                               REWRITE
ydlidar_ros2_driver     package.xml                                  EDIT
ydlidar_ros2_driver     params/ydlidar.yaml                          EDIT

cartographer            cartographer/common/absl_condition.h         ADDED
cartographer            CMakeLists.txt                               EDIT
cartographer            cartographer/common/task.cc                  EDIT
cartographer            cartographer/common/thread_pool.cc           EDIT
cartographer            cartographer/common/internal/blocking_queue.h
                                                                     EDIT
cartographer            cartographer/common/internal/testing/
                          thread_pool_for_testing.cc                 EDIT
cartographer            cartographer/mapping/internal/2d/
                          pose_graph_2d.cc                           EDIT
cartographer            cartographer/mapping/internal/3d/
                          pose_graph_3d.cc                           EDIT

cartographer_ros        cartographer_ros_msgs/COLCON_IGNORE          ADDED
cartographer_ros        cartographer_rviz/COLCON_IGNORE              ADDED
cartographer_ros        cartographer_ros/CMakeLists.txt              EDIT
cartographer_ros        cartographer_ros/src/node_main.cpp           EDIT


================================================================================
1. ydlidar_sdk
================================================================================
Upstream : https://github.com/YDLIDAR/YDLidar-SDK
Commit   : (no SHA recorded)  version 1.2.6    vendored 2026-09-07
Why      : no Lyrical binary; driver needs this C++ SDK
Build    : colcon build --symlink-install --packages-select ydlidar_sdk

ADDED
    package.xml
        cmake package so colcon can find it
        build_type = cmake

EDITED
    CMakeLists.txt
        cmake_minimum_required 2.8 -> 3.8
        BUILD_EXAMPLES default OFF

    core/CMakeLists.txt
        cmake_minimum_required 2.8 -> 3.8

    examples/CMakeLists.txt
        cmake_minimum_required 2.8 -> 3.8

    cmake/install_package.cmake
        modern CMake: do not install export() Targets.cmake
        install(TARGETS) instead of install(FILES LOCATION)
        drop obsolete cmake_policy(... OLD) where it broke configure

NOT TOUCHED
    all lidar protocol / driver .cpp .h


================================================================================
2. ydlidar_ros2_driver
================================================================================
Upstream : https://github.com/YDLIDAR/ydlidar_ros2_driver  branch humble
Commit   : (no SHA recorded)  version 1.0.1    vendored 2026-09-07
Why      : no Lyrical binary; real robot /scan
Build    : colcon build --symlink-install --packages-select ydlidar_ros2_driver
Run      : tortoisebot_bringup when use_sim_time:=False

EDITED
    CMakeLists.txt
        REWRITTEN for Lyrical
        ament_target_dependencies does not exist
        now: target_link_libraries(rclcpp::rclcpp sensor_msgs::... ydlidar_sdk)

    package.xml
        added <depend>ydlidar_sdk</depend>

    params/ydlidar.yaml
        frame_id: lidar
        port: /dev/ttyUSB0

NOT TOUCHED
    src/ydlidar_ros2_driver_node.cpp
    src/ydlidar_ros2_driver_client.cpp
    launch/*.py   (bringup starts the node itself; do not use vendor
                   ydlidar_launch.py — it publishes extra laser_frame TF)


================================================================================
3. cartographer
================================================================================
Upstream : https://github.com/ros2/cartographer.git  branch ros2
Commit   : 1489fc933b6e0b1da936ca08af462abe559dd02e
           tag 2.0.9004    vendored 2026-09-07
Why      : Lyrical has no cartographer apt binary
           TortoiseBot uses it for lidar-only odom
Build    : colcon build --symlink-install --packages-select cartographer

ADDED
    cartographer/common/absl_condition.h
        MakeCondition() helper
        Abseil 2026 no longer accepts capturing lambdas as
        absl::Condition(&predicate)

EDITED
    CMakeLists.txt
        map old thread-annotation macros to ABSL_*
        GUARDED_BY, LOCKS_EXCLUDED, EXCLUSIVE_LOCKS_REQUIRED, ...

    cartographer/common/task.cc
        never hold Task::mutex_ while locking another mutex
        Abseil 2026 aborts on the upstream Execute ->
        OnDependenyCompleted lock order (exit -6)

    cartographer/common/thread_pool.cc
        include absl_condition.h
        absl::Condition(&predicate) -> MakeCondition(&predicate)

    cartographer/common/internal/blocking_queue.h
        same Condition swap (6 call sites)

    cartographer/common/internal/testing/thread_pool_for_testing.cc
        same Condition swap

    cartographer/mapping/internal/2d/pose_graph_2d.cc
        same Condition swap (2 call sites)

    cartographer/mapping/internal/3d/pose_graph_3d.cc
        same Condition swap (2 call sites)

NOT TOUCHED
    scan matching, lua configs we ship, occupancy math
    tortoisebot lua lives in src/tortoisebot_slam/config/


================================================================================
4. cartographer_ros
================================================================================
Upstream : https://github.com/ros2/cartographer_ros.git  branch ros2
Commit   : 743345256b43a7fd95765d40c7332b6f31ab66bb
           version 2.0.9003    vendored 2026-09-07
Why      : ROS wrapper; nodes cartographer_node and
           cartographer_occupancy_grid_node
Build    : colcon build --symlink-install --packages-select cartographer_ros
Run      : tortoisebot_slam/launch/cartographer_slam.launch.py

ADDED
    cartographer_ros_msgs/COLCON_IGNORE
        use apt ros-lyrical-cartographer-ros-msgs instead

    cartographer_rviz/COLCON_IGNORE
        we do not need the RViz plugin

EDITED
    cartographer_ros/CMakeLists.txt
        same ABSL_* annotation aliases as cartographer

    cartographer_ros/src/node_main.cpp
        overlapping gflags already defined in the shared library
        (offline_node.cpp). Changed those to DECLARE_* so
        cartographer_node can start:
            collect_metrics
            configuration_directory
            load_state_filename
            load_frozen_state
            save_state_filename
        left DEFINE for configuration_basename and
        start_trajectory_with_default_topics

NOT TOUCHED
    occupancy_grid_node_main.cpp
    launch files inside this vendor tree
    our lua / tortoisebot_slam launch


================================================================================
IF YOU UPGRADE THE UPSTREAM CLONE
================================================================================
    1. Copy the upstream tree here.
    2. Record the new commit (or version) in PINNED UPSTREAM above.
    3. Re-apply only the files in the table.
    4. Add a line here for anything new.
    5. Rebuild:  colcon build --symlink-install --packages-select <package>
    6. Check:    ros2 pkg list | grep -E 'cartographer|ydlidar'
    7. For Cartographer, start cartographer_node with cartographer.config.lua.
================================================================================
