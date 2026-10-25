option(COUNTER_BUILD_TESTS "Build this example's independent tests" ON)
if(COUNTER_BUILD_TESTS)
    enable_testing()
    add_executable(counter_lifecycle_tests "${CMAKE_CURRENT_LIST_DIR}/lifecycle.cpp")
    target_compile_features(counter_lifecycle_tests PRIVATE cxx_std_23)
    set_target_properties(counter_lifecycle_tests PROPERTIES
        CXX_EXTENSIONS OFF
        MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>DLL"
    )
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
        -P "${CMAKE_CURRENT_LIST_DIR}/shell.cmake"
    )
    set_tests_properties(counter.shell PROPERTIES TIMEOUT 30 RUN_SERIAL TRUE)
endif()
