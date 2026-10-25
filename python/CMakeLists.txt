cmake_minimum_required(VERSION 3.20)
project(open_vinc_python_tutorials LANGUAGES C CXX)

set(VINC_NAME "python-tutorials" CACHE STRING "Central instance identity")
set(VINC_BUILD_EXAMPLES OFF CACHE BOOL "Build the framework's own examples")
set(VINC_BUILD_UI OFF CACHE BOOL "Build the runtime Web UI")
set(VINC_BUILD_PYTHON ON CACHE BOOL "Build the Python SDK")
set(BUILD_TESTING OFF CACHE BOOL "Build the framework's internal tests")

add_subdirectory(../framework/open-vinc/src open-vinc)
add_message_dir("${CMAKE_CURRENT_SOURCE_DIR}/../messages")

set_target_properties(shell PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}"
    RUNTIME_OUTPUT_DIRECTORY_DEBUG "${CMAKE_BINARY_DIR}"
    RUNTIME_OUTPUT_DIRECTORY_RELEASE "${CMAKE_BINARY_DIR}"
)

include(cmake/DeployModules.cmake)
include(tests/CMakeLists.txt)
