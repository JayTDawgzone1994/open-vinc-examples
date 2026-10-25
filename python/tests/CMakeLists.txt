option(PYTHON_TUTORIAL_BUILD_TESTS "Test the Python tutorials" ON)
if(PYTHON_TUTORIAL_BUILD_TESTS)
    enable_testing()
    add_test(NAME python.tutorials COMMAND "${Python_EXECUTABLE}"
        "${CMAKE_CURRENT_LIST_DIR}/smoke.py" "$<TARGET_FILE:shell>"
        "${Python_EXECUTABLE}" "${CMAKE_CURRENT_BINARY_DIR}/python-test.log"
    )
    set_tests_properties(python.tutorials PROPERTIES TIMEOUT 90 RUN_SERIAL TRUE)
endif()
