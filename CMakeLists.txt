cmake_minimum_required(VERSION 3.20)
project(open_vinc_counter_example LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
if(MSVC)
    set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>DLL")
    add_compile_options("$<$<COMPILE_LANGUAGE:CXX>:/utf-8>")
endif()

set(VINC_NAME "counter-example" CACHE STRING "Central instance identity")
set(VINC_BUILD_APPS ON CACHE BOOL "Build the central executable")
set(VINC_BUILD_EXAMPLES OFF CACHE BOOL "Build the framework's own examples")
set(VINC_BUILD_UI OFF CACHE BOOL "Build the runtime Web UI")
set(VINC_BUILD_PYTHON OFF CACHE BOOL "Build the Python SDK")
set(BUILD_TESTING OFF CACHE BOOL "Build the framework's internal tests")
option(COUNTER_BUILD_TESTS "Build this example's independent tests" ON)

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

if(COUNTER_BUILD_TESTS)
    enable_testing()
    add_executable(counter_lifecycle_tests tests/lifecycle.cpp)
    target_link_libraries(counter_lifecycle_tests PRIVATE vinc::module_manager vinc::errors)
    add_dependencies(counter_lifecycle_tests counter_publisher counter_subscriber)
    add_test(NAME counter.lifecycle COMMAND counter_lifecycle_tests
        "$<TARGET_FILE:vinc_module_host>"
        "$<TARGET_FILE:counter_publisher>"
        "$<TARGET_FILE:counter_subscriber>"
    )
    set_tests_properties(counter.lifecycle PROPERTIES TIMEOUT 40 RUN_SERIAL TRUE)

    add_test(NAME counter.shell COMMAND "${CMAKE_COMMAND}"
        "-DAPP=$<TARGET_FILE:shell>"
        "-DSTARTUP_SCRIPT=${CMAKE_CURRENT_SOURCE_DIR}/scripts/startup.tcl"
        "-DTEST_DIRECTORY=${CMAKE_CURRENT_BINARY_DIR}/shell-test"
        -P "${CMAKE_CURRENT_SOURCE_DIR}/tests/shell.cmake"
    )
    set_tests_properties(counter.shell PROPERTIES TIMEOUT 30 RUN_SERIAL TRUE)
endif()
