cmake_minimum_required(VERSION 3.16)
project(virtual_engine_controller LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_library(engine_controller
    src/engine_controller.cpp
)
target_include_directories(engine_controller PUBLIC include)
target_compile_options(engine_controller PRIVATE -Wall -Wextra -Wpedantic)

add_executable(virtual_ecu
    src/main.cpp
    src/can_handler.cpp
)
target_link_libraries(virtual_ecu PRIVATE engine_controller)
target_compile_options(virtual_ecu PRIVATE -Wall -Wextra -Wpedantic)

include(CTest)
if(BUILD_TESTING)
    add_executable(engine_controller_test tests/engine_controller_test.cpp)
    target_link_libraries(engine_controller_test PRIVATE engine_controller)
    target_compile_options(engine_controller_test PRIVATE -Wall -Wextra -Wpedantic)
    add_test(NAME engine_controller_test COMMAND engine_controller_test)
endif()
