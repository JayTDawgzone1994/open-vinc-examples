cmake_minimum_required(VERSION 3.20)
project(open_vinc_first_module LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
if(MSVC)
    set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>DLL")
    add_compile_options("$<$<COMPILE_LANGUAGE:CXX>:/utf-8>")
endif()

set(VINC_NAME "first-module-example" CACHE STRING "Central instance identity")
set(VINC_BUILD_APPS ON CACHE BOOL "Build the central executable")
set(VINC_BUILD_EXAMPLES OFF CACHE BOOL "Build the framework's own examples")
set(VINC_BUILD_UI OFF CACHE BOOL "Build the runtime Web UI")
set(VINC_BUILD_PYTHON OFF CACHE BOOL "Build the Python SDK")
set(BUILD_TESTING OFF CACHE BOOL "Build the framework's internal tests")
option(FIRST_MODULE_BUILD_TESTS "Build this example's independent tests" ON)

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

if(FIRST_MODULE_BUILD_TESTS)
    enable_testing()
    add_test(NAME hello.shell COMMAND "${CMAKE_COMMAND}"
        "-DAPP=$<TARGET_FILE:shell>"
        "-DSTARTUP_SCRIPT=${CMAKE_CURRENT_SOURCE_DIR}/scripts/startup.tcl"
        "-DTEST_DIRECTORY=${CMAKE_CURRENT_BINARY_DIR}/hello-test"
        -P "${CMAKE_CURRENT_SOURCE_DIR}/tests/shell.cmake"
    )
    set_tests_properties(hello.shell PROPERTIES TIMEOUT 30 RUN_SERIAL TRUE)
endif()
