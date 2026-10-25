cmake_minimum_required(VERSION 3.20)
project(open_vinc_counter_example LANGUAGES C CXX)

if(MSVC)
    add_compile_options("$<$<COMPILE_LANGUAGE:CXX>:/utf-8>")
endif()

set(VINC_NAME "counter-example" CACHE STRING "Central instance identity")
set(VINC_BUILD_EXAMPLES OFF CACHE BOOL "Build the framework's own examples")
set(VINC_BUILD_UI OFF CACHE BOOL "Build the runtime Web UI")
set(BUILD_TESTING OFF CACHE BOOL "Build the framework's internal tests")

add_subdirectory(framework/open-vinc/src open-vinc)
add_message_dir("${CMAKE_CURRENT_SOURCE_DIR}/messages")

add_module(counter_publisher
    MODULE_TYPE_NAME counterPublisher
    SOURCES modules/publisher.cpp
)
add_module(counter_subscriber
    MODULE_TYPE_NAME counterSubscriber
    SOURCES modules/subscriber.cpp
)

# Keep the tutorial's executable path stable. Tcl deployment follows this target.
set_target_properties(shell PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}"
    RUNTIME_OUTPUT_DIRECTORY_DEBUG "${CMAKE_BINARY_DIR}"
    RUNTIME_OUTPUT_DIRECTORY_RELEASE "${CMAKE_BINARY_DIR}"
)

include(tests/CMakeLists.txt)
