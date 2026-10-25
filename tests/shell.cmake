cmake_minimum_required(VERSION 3.20)
file(MAKE_DIRECTORY "${TEST_DIRECTORY}")
file(TO_CMAKE_PATH "${STARTUP_SCRIPT}" startup)
file(WRITE "${TEST_DIRECTORY}/smoke.tcl"
    "set failure [catch {\nsource {${startup}}\nsender send\nreceiver status\n"
    "if {![catch {sender invalid}]} {error {invalid command unexpectedly succeeded}}\n"
    "receiver reset\nreceiver status\n"
    "if {![catch {receiver invalid}]} {error {invalid receiver command unexpectedly succeeded}}\n"
    "if {![catch {receiver reset extra}]} {error {extra reset argument unexpectedly succeeded}}\n"
    "} detail]\nputs \"COUNTER_RESULT=$failure $detail\"\nexit\n")
execute_process(
    COMMAND "${APP}" --shell-port 0 -S "${TEST_DIRECTORY}/smoke.tcl"
    WORKING_DIRECTORY "${TEST_DIRECTORY}"
    RESULT_VARIABLE result OUTPUT_VARIABLE output ERROR_VARIABLE errors TIMEOUT 20
    ENCODING UTF-8
)
file(WRITE "${TEST_DIRECTORY}/output.log" "${output}\n${errors}")
if(NOT result STREQUAL "0")
    message(FATAL_ERROR "Vinc failed (${result}): ${output} ${errors}")
endif()
foreach(marker IN ITEMS "ready sender" "ready receiver" "counter reset" "COUNTER_RESULT=0" "stopped sender" "stopped receiver")
    if(NOT "${output}${errors}" MATCHES "${marker}")
        message(FATAL_ERROR "Missing ${marker}: ${output} ${errors}")
    endif()
endforeach()
message(STATUS "Real Vinc startup script, command error and orderly exit passed")
