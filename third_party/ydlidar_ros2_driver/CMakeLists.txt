# Copyright(c) 2020 eaibot limited.
# Minimal Lyrical port: ament_target_dependencies was removed.
cmake_minimum_required(VERSION 3.10)
project(ydlidar_ros2_driver C CXX)

if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 17)
endif()
if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  # Hide Lyrical / SDK header noise. Do not restyle vendor C++.
  add_compile_options(-w)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(visualization_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(std_srvs REQUIRED)
find_package(ydlidar_sdk REQUIRED)

find_library(YDLIDAR_SDK_STATIC_LIB
  NAMES ydlidar_sdk
  PATHS ${CMAKE_PREFIX_PATH}
  PATH_SUFFIXES lib
  REQUIRED
)
message(STATUS "Found ydlidar_sdk library: ${YDLIDAR_SDK_STATIC_LIB}")

add_executable(${PROJECT_NAME}_node
  src/${PROJECT_NAME}_node.cpp)
target_include_directories(${PROJECT_NAME}_node PRIVATE
  ${PROJECT_SOURCE_DIR}
  ${PROJECT_SOURCE_DIR}/src
  ${YDLIDAR_SDK_INCLUDE_DIRS})
target_link_libraries(${PROJECT_NAME}_node
  rclcpp::rclcpp
  sensor_msgs::sensor_msgs
  visualization_msgs::visualization_msgs
  geometry_msgs::geometry_msgs
  std_srvs::std_srvs
  ${YDLIDAR_SDK_STATIC_LIB}
  pthread
  rt)

add_executable(${PROJECT_NAME}_client
  src/${PROJECT_NAME}_client.cpp)
target_link_libraries(${PROJECT_NAME}_client
  rclcpp::rclcpp
  sensor_msgs::sensor_msgs
  visualization_msgs::visualization_msgs
  geometry_msgs::geometry_msgs
  std_srvs::std_srvs)

install(TARGETS
  ${PROJECT_NAME}_node ${PROJECT_NAME}_client
  DESTINATION lib/${PROJECT_NAME})

install(DIRECTORY launch params startup config
  DESTINATION share/${PROJECT_NAME})

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
