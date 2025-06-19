cmake_minimum_required(VERSION 3.16)
project(STEPViewer)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Detect an Emscripten build and forward to the web version
if (CMAKE_SYSTEM_NAME STREQUAL "Emscripten")
    include(${CMAKE_CURRENT_LIST_DIR}/CMakeLists_emscripten.cmake)
    return()             # stop processing the native script
endif()

# Find OpenCASCADE
find_package(OpenCASCADE REQUIRED)

if(OpenCASCADE_FOUND)
    message(STATUS "OpenCASCADE found at: ${OpenCASCADE_INSTALL_PREFIX}")
    message(STATUS "OpenCASCADE include dirs: ${OpenCASCADE_INCLUDE_DIR}")
    message(STATUS "OpenCASCADE libraries: ${OpenCASCADE_LIBRARIES}")
else()
    message(FATAL_ERROR "OpenCASCADE not found!")
endif()

# Include OpenCASCADE headers
include_directories(${OpenCASCADE_INCLUDE_DIR})

# Add executable
add_executable(step_viewer src/main.cpp)

# Link OpenCASCADE libraries
target_link_libraries(step_viewer ${OpenCASCADE_LIBRARIES})

# For macOS, you might need additional frameworks
if(APPLE)
    find_library(COCOA_LIBRARY Cocoa)
    find_library(OPENGL_LIBRARY OpenGL)
    if(COCOA_LIBRARY)
        target_link_libraries(step_viewer ${COCOA_LIBRARY})
    endif()
    if(OPENGL_LIBRARY)
        target_link_libraries(step_viewer ${OPENGL_LIBRARY})
    endif()
endif()

# Add compiler flags for better compatibility
if(CMAKE_CXX_COMPILER_ID MATCHES "Clang" OR CMAKE_CXX_COMPILER_ID MATCHES "GNU")
    target_compile_options(step_viewer PRIVATE -Wall -Wextra)
endif()

# For Emscripten build
if(EMSCRIPTEN)
    set_target_properties(step_viewer PROPERTIES
        COMPILE_FLAGS "-s USE_WEBGL2=1 -s USE_FREETYPE=1"
        LINK_FLAGS "-s USE_WEBGL2=1 -s WASM=1 --bind -s ALLOW_MEMORY_GROWTH=1"
    )
endif()