# TortoiseBot

Open-source differential-drive robot designed and sold by RigBetel Labs
(https://rigbetellabs.com/tortoisebot/). Two driven wheels, a rear caster, a
360° lidar, and a Raspberry Pi camera. The kit is meant for learning ROS:
teleop, mapping, and Nav2 on hardware that stays cheap by skipping wheel
encoders.

This folder is the robot model used by tortoisebot_description: COLLADA meshes
plus xacro that robot_state_publisher loads as /robot_description.

## What it is

- Drive: two-wheel differential, 60 RPM BO motors, L298N dual H-bridge, one rear caster.
- Computer: Raspberry Pi 4 Model B (kit default 2 GB), Raspberry Pi OS /
  Ubuntu, GPIO PWM to the driver.
- Sensors (kit): YDLiDAR S2 on USB (/dev/ttyUSB0), Raspberry Pi Camera Rev 1.3
  (5 MP) on CSI.
- Power: 11.1 V 2200 mAh Li-ion to the motor driver; USB voltage stabilizer to
  5 V for the Pi. Idle on the order of 4+ hours, run time 1+ hour. Payload
  about 1.1 kg on top of the robot's own mass.
- Odometry: no wheel encoders. On the Pi, Cartographer publishes the odom TF
  (use_odometry = false, provide_odom_frame = true). Gazebo Sim publishes /odom
  and TF via ros_gz_bridge.

This workspace runs that robot on ROS 2 Lyrical. Gazebo Sim 10 uses the same
geometry; Classic Gazebo is not used.

## Geometry (this URDF)

Values in urdf/tortoisebot.xacro. Wheel diameter and separation match the
firmware defaults.

  Item                              Value
  --------------------------------  ----------------
  Wheel diameter                    65 mm (radius 0.0325 m)
  Wheel width (sim collision)       20 mm
  Wheel separation                  0.17186 m
  Max linear velocity               0.20 m/s
  Max angular velocity              1.5 rad/s
  Caster radius                     5 mm
  Caster ball                       0.077 m
  Base mass (inertial)              1.129 kg
  Each drive wheel                  0.044 kg
  Lidar link                        0.026 kg
  Approx. URDF mass                 ~1.25 kg

Motor RPM 60 at 65 mm wheels is about 0.20 m/s at the rim, which is the cap
used in Nav2 and Gazebo.

## Hardware (kit)

  Part           Detail
  -------------  --------------------------------------------------------------
  Chassis        Laser-cut stacked plates, 45 mm M3 hex spacers
  Motors         2 × 60 RPM BO, metal brackets + 3D-printed mounts
  Wheels         2 × 65 mm BO wheels
  Caster         1 rear caster
  Driver         L298N, 2 A per channel
  SBC            Raspberry Pi 4 Model B
  Storage        Class 10 microSD (kit often 16–32 GB)
  Camera         Raspberry Pi Camera Rev 1.3, 5 MP, 3D-printed pitch mount
  Lidar          YDLiDAR S2 kit (module, USB cable, converter). Product listing
                 ~8 m; driver 0.1–12 m, Gazebo 0.12–12 m, 10 Hz, 360 samples
  Battery        11.1 V 2200 mAh Li-ion + 12 V charger + voltage checker

### GPIO (this firmware)

BCM numbering in tortoisebot_firmware differential.
L298N: ENA/ENB PWM, IN1–IN4 direction.

  Function                     BCM
  ---------------------------  ------
  Left PWM (ENA)               13
  Right PWM (ENB)              12
  Left forward / backward      6 / 5
  Right forward / backward     16 / 20
  PWM frequency                100 Hz
  PWM range                    15–100

## Sensors in simulation

tortoisebot_sim.xacro holds the Gazebo Sim plugins (diff-drive, joint state,
lidar, camera). tortoisebot_gazebo only owns worlds, bridges, and gz launch.

  Sensor      Topic                 Notes
  ----------  --------------------  ------------------------------------------
  GPU lidar   /scan                 10 Hz, 360 samples, 0.12–12 m,
                                    frame_id = robot_front_laser_base_link
  Camera      /camera/image_raw     5 Hz, 800×600, HFOV 1.086 rad (~62°)
  Diff drive  /cmd_vel, /odom       wheel radius / separation from the xacro;
                                    TF from the plugin is off

On the real robot the same /scan and /camera/image_raw topics come from
ydlidar_ros2_driver and camera_ros (800×600 RGB888, remapped), not Gazebo.

## Files

models/
├── readme.txt                  # this file
├── urdf/
│   ├── tortoisebot.xacro       # shared links, joints, inertias, meshes
│   ├── tortoisebot_sim.xacro   # sim entry + Gazebo Sim plugins / sensors
│   └── tortoisebot_real.xacro
└── meshes/                     # millimetre COLLADA, scaled 0.001 in xacro
    ├── base_link.dae
    ├── wheel_left.dae
    ├── wheel_right.dae
    ├── lidar.dae
    ├── camera_holder.dae
    ├── camera_link.dae
    └── castor_wheel.dae

use_sim_time:=True loads tortoisebot_sim.xacro. Otherwise tortoisebot_real.xacro
(same body, no <gazebo> tags, mesh collisions on the wheels). Launch:
tortoisebot_description state_publisher.launch.py.

## Frames

odom → robot_base_footprint → robot_base_link, then:

  Link                           Joint               Role
  -----------------------------  ------------------  -------------
  robot_left_wheel               continuous, Y axis  drive
  robot_right_wheel              continuous, Y axis  drive
  robot_front_laser_base_link    fixed               lidar
  robot_camera_holder_link       fixed               camera holder
  robot_front_camera_link        fixed               camera
  robot_caster_wheel             fixed               rear caster

Cartographer tracks robot_base_footprint. Nav2 robot_base_frame is robot_base_link.

## ROS topics used with this model

  Topic                      Role
  -------------------------  -------------------------------------------
  /cmd_vel                   twist_mux → motors / Gazebo
  /cmd_vel_web               web teleop
  /cmd_vel_key               keyboard teleop
  /cmd_vel_nav2              Nav2 velocity smoother
  /odom                      Gazebo topic in sim; Cartographer TF on Pi
  /scan                      lidar
  /camera/image_raw          camera (sim bridge or camera_ros)
  /lpwm /rpwm /ldir /rdir    motor debug

## References

- RigBetel Labs — TortoiseBot
  https://rigbetellabs.com/tortoisebot/
- rigbetellabs/tortoisebot
  https://github.com/rigbetellabs/tortoisebot
- Wiki: getting started
  https://github.com/rigbetellabs/tortoisebot/wiki/1.-Getting-Started-Overview
- Wiki: features / BOM
  https://github.com/rigbetellabs/tortoisebot/wiki/Features
