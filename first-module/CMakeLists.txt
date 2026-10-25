cmake_minimum_required(VERSION 3.20)
project(open_vinc_first_module LANGUAGES C CXX)

if(MSVC)
    add_compile_options("$<$<COMPILE_LANGUAGE:CXX>:/utf-8>")
endif()

set(VINC_NAME "first-module-example" CACHE STRING "Central instance identity")
set(VINC_BUILD_EXAMPLES OFF CACHE BOOL "Build the framework's own examples")
set(VINC_BUILD_UI OFF CACHE BOOL "Build the runtime Web UI")
set(BUILD_TESTING OFF CACHE BOOL "Build the framework's internal tests")

add_subdirectory(../framework/open-vinc/src open-vinc)

add_module(hello_module
    MODULE_TYPE_NAME helloModule
    SOURCES hello.cpp
)

# Keep the tutorial's executable path stable. Tcl deployment follows this target.
set_target_properties(shell PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}"
    RUNTIME_OUTPUT_DIRECTORY_DEBUG "${CMAKE_BINARY_DIR}"
    RUNTIME_OUTPUT_DIRECTORY_RELEASE "${CMAKE_BINARY_DIR}"
)

include(tests/CMakeLists.txt)
