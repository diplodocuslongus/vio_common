cmake_minimum_required(VERSION 3.5.1)
project(TimestampCorrector)
set(CMAKE_BUILD_TYPE "Release")
find_package(pybind11 REQUIRED)
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/include 
                    /usr/include/python3.8)
# include_directories(${CMAKE_CURRENT_SOURCE_DIR}/include ${pybind11_INCLUDE_DIRS})
pybind11_add_module(TimestampCorrector src/exportTimestampCorrector.cpp)
