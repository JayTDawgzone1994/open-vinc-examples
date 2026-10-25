add_custom_target(python_tutorial_modules ALL
    COMMAND "${CMAKE_COMMAND}" -E copy_directory
        "${CMAKE_CURRENT_SOURCE_DIR}/modules"
        "$<TARGET_FILE_DIR:shell>/data/module"
    VERBATIM
)
add_dependencies(shell python_tutorial_modules)
