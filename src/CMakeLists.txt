
include_directories (${CMAKE_SOURCE_DIR}/include)

set(SOURCES lcs_cli.cpp ${CMAKE_SOURCE_DIR}/src/LCS.cpp ${CMAKE_SOURCE_DIR}/src/Tools.cpp)
add_executable (lcs ${SOURCES}) 

set(SOURCES augmentInputMatches_cli.cpp ${CMAKE_SOURCE_DIR}/src/LCS.cpp ${CMAKE_SOURCE_DIR}/src/Align.cpp ${CMAKE_SOURCE_DIR}/src/Tools.cpp)
add_executable (augmentInputMatches ${SOURCES}) 


