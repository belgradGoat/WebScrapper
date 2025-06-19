cmake_minimum_required(VERSION 3.16)
project(STEPViewer)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Detect an Emscripten build
if (CMAKE_SYSTEM_NAME STREQUAL "Emscripten" OR EMSCRIPTEN)
    # For Emscripten builds, only set up the web version
    add_executable(step_viewer src/main_web.cpp)
    
    set_target_properties(step_viewer PROPERTIES
        COMPILE_FLAGS "-O2"
        LINK_FLAGS "-O2 -s WASM=1 -s ALLOW_MEMORY_GROWTH=1 -s EXPORTED_FUNCTIONS='[\"_main\",\"_initApp\",\"_loadSTEPFile\",\"_createUCS\",\"_takeScreenshot\",\"_saveSTEPCopy\",\"_getUCSInfo\",\"_getBoundingBoxInfo\",\"_getVertexCount\",\"_getNormalCount\",\"_getIndexCount\",\"_getVertices\",\"_getNormals\",\"_getIndices\"]' -s EXPORTED_RUNTIME_METHODS='[\"ccall\",\"cwrap\",\"FS\",\"HEAPF32\",\"HEAPU32\"]' -s MODULARIZE=1 -s EXPORT_NAME='createModule'"
    )
else()
    # Native build configuration
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

    # Add executable for native build
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
endif()