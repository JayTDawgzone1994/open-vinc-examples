option(FIRST_MODULE_BUILD_TESTS "Build this example's independent tests" ON)
if(FIRST_MODULE_BUILD_TESTS)
    enable_testing()
    add_test(NAME hello.shell COMMAND "${CMAKE_COMMAND}"
        "-DAPP=$<TARGET_FILE:shell>"
        "-DSTARTUP_SCRIPT=${CMAKE_CURRENT_SOURCE_DIR}/scripts/startup.tcl"
        "-DTEST_DIRECTORY=${CMAKE_CURRENT_BINARY_DIR}/hello-test"
        -P "${CMAKE_CURRENT_LIST_DIR}/shell.cmake"
    )
    set_tests_properties(hello.shell PROPERTIES TIMEOUT 30 RUN_SERIAL TRUE)
endif()
