cmake_minimum_required( VERSION 2.8 )
set(CMAKE_BUILD_TYPE Release)
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)

project (corpora-tools)
add_subdirectory(src)
