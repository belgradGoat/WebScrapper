#!/bin/bash
# filepath: /Users/sebastianszewczyk/Documents/GitHub/WebScrapper/STEPViewer/build_web.sh

echo "Building STEP Viewer for Web..."

# Clean previous build
rm -rf build_web
mkdir build_web
cd build_web

# Configure with Emscripten
emcmake cmake ..

# Build
emmake make

# Check if build was successful
if [ -f "step_viewer.js" ] && [ -f "step_viewer.wasm" ]; then
    echo "Build successful!"
    echo "Generated files:"
    ls -la step_viewer.*
    
    # Copy to parent directory for easy access
    cp step_viewer.js ../
    cp step_viewer.wasm ../
    
    echo "Files copied to parent directory"
else
    echo "Build failed!"
    exit 1
fi