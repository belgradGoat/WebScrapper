cmake_minimum_required(VERSION 3.16)
project(STEPViewerWeb)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Add executable
add_executable(step_viewer src/main_web.cpp)

# Emscripten-specific settings
if(EMSCRIPTEN)
    set_target_properties(step_viewer PROPERTIES
        COMPILE_FLAGS "-O2"
        LINK_FLAGS "-O2 -s WASM=1 -s ALLOW_MEMORY_GROWTH=1 -s EXPORTED_FUNCTIONS='[\"_main\",\"_initApp\",\"_loadSTEPFile\",\"_createUCS\",\"_takeScreenshot\",\"_saveSTEPCopy\",\"_getUCSInfo\",\"_getBoundingBoxInfo\",\"_getVertexCount\",\"_getNormalCount\",\"_getIndexCount\",\"_getVertices\",\"_getNormals\",\"_getIndices\"]' -s EXPORTED_RUNTIME_METHODS='[\"ccall\",\"cwrap\",\"FS\",\"HEAPF32\",\"HEAPU32\"]' -s MODULARIZE=1 -s EXPORT_NAME='createModule'"
    )
endif()