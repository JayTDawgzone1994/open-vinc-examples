cmake_minimum_required(VERSION 3.20)
file(MAKE_DIRECTORY "${TEST_DIRECTORY}")
file(TO_CMAKE_PATH "${STARTUP_SCRIPT}" startup)
file(WRITE "${TEST_DIRECTORY}/smoke.tcl"
    "set failure [catch {source {${startup}}} detail]\n"
    "puts \"HELLO_RESULT=$failure $detail\"\n"
    "exit\n")
execute_process(
    COMMAND "${APP}" --shell-port 0 -S "${TEST_DIRECTORY}/smoke.tcl"
    WORKING_DIRECTORY "${TEST_DIRECTORY}"
    RESULT_VARIABLE result
    OUTPUT_VARIABLE output
    ERROR_VARIABLE errors
    TIMEOUT 20
    ENCODING UTF-8
)
file(WRITE "${TEST_DIRECTORY}/output.log" "${output}\n${errors}")
if(NOT result STREQUAL "0")
    message(FATAL_ERROR "Vinc failed (${result}): ${output} ${errors}")
endif()
foreach(marker IN ITEMS "hello started" "HELLO_RESULT=0" "hello stopped")
    if(NOT "${output}${errors}" MATCHES "${marker}")
        message(FATAL_ERROR "Missing ${marker}: ${output} ${errors}")
    endif()
endforeach()
string(FIND "${output}" "hello started" start_position)
string(FIND "${output}" "hello stopped" stop_position)
if(start_position GREATER_EQUAL stop_position)
    message(FATAL_ERROR "Lifecycle output is out of order: ${output} ${errors}")
endif()
message(STATUS "Real Vinc, hello Plugin startup and normal exit passed")
