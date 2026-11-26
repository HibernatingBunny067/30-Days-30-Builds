cmake_minimum_required(VERSION 3.20)
project(lbm_wind_tunnel CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)  # lets your editor find headers

if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release)  # -O3; use -DCMAKE_BUILD_TYPE=Debug when stepping through code
endif()

add_executable(lbm
  src/main.cpp
  src/simulation.cpp
  src/image.cpp
)
target_compile_options(lbm PRIVATE -Wall -Wextra -Wpedantic)
