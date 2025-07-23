#!/bin/bash

# WebScraper Multi-Tool Repository Component Evaluation Script
# This script evaluates the status of all components and provides recommendations

echo "🌟 WebScraper Multi-Tool Repository - Component Evaluation"
echo "======================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if a directory exists and has required files
check_component() {
    local component_name=$1
    local component_path=$2
    local required_files=$3
    local status="✅ Ready"
    local issues=""
    
    echo -e "${BLUE}Checking $component_name...${NC}"
    
    if [ ! -d "$component_path" ]; then
        status="❌ Missing"
        issues="Directory not found"
    else
        cd "$component_path"
        
        # Check for required files
        IFS=',' read -ra FILES <<< "$required_files"
        for file in "${FILES[@]}"; do
            if [ ! -f "$file" ]; then
                if [ "$status" = "✅ Ready" ]; then
                    status="⚠️ Issues"
                fi
                issues="${issues}Missing: $file; "
            fi
        done
        
        cd - > /dev/null
    fi
    
    printf "  %-20s %s\n" "$component_name" "$status"
    if [ ! -z "$issues" ]; then
        echo "    Issues: $issues"
    fi
    echo ""
}

# Function to check Node.js components
check_node_component() {
    local component_name=$1
    local component_path=$2
    
    echo -e "${BLUE}Checking $component_name (Node.js)...${NC}"
    
    if [ ! -d "$component_path" ]; then
        printf "  %-20s %s\n" "$component_name" "❌ Missing"
        echo "    Directory not found"
        echo ""
        return
    fi
    
    cd "$component_path"
    
    local status="✅ Ready"
    local issues=""
    
    # Check package.json
    if [ ! -f "package.json" ]; then
        status="❌ Error"
        issues="${issues}Missing package.json; "
    fi
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        if [ "$status" = "✅ Ready" ]; then
            status="⚠️ Setup Needed"
        fi
        issues="${issues}Run npm install; "
    fi
    
    # Try to get npm scripts
    if [ -f "package.json" ]; then
        local scripts=$(node -p "Object.keys(require('./package.json').scripts || {})" 2>/dev/null || echo "[]")
        if [ "$scripts" != "[]" ]; then
            echo "    Available scripts: $scripts"
        fi
    fi
    
    cd - > /dev/null
    
    printf "  %-20s %s\n" "$component_name" "$status"
    if [ ! -z "$issues" ]; then
        echo "    Issues: $issues"
    fi
    echo ""
}

# Function to check Python components
check_python_component() {
    local component_name=$1
    local component_path=$2
    
    echo -e "${BLUE}Checking $component_name (Python)...${NC}"
    
    if [ ! -d "$component_path" ]; then
        printf "  %-20s %s\n" "$component_name" "❌ Missing"
        echo ""
        return
    fi
    
    cd "$component_path"
    
    local status="✅ Ready"
    local issues=""
    
    # Check for requirements.txt or main.py
    if [ -f "requirements.txt" ]; then
        echo "    Found requirements.txt"
        # Try to check if requirements are installed (basic check)
        if ! python3 -c "import numpy" 2>/dev/null && grep -q "numpy" requirements.txt; then
            if [ "$status" = "✅ Ready" ]; then
                status="⚠️ Dependencies"
            fi
            issues="${issues}Run pip install -r requirements.txt; "
        fi
    fi
    
    if [ -f "main.py" ]; then
        echo "    Found main.py"
    fi
    
    cd - > /dev/null
    
    printf "  %-20s %s\n" "$component_name" "$status"
    if [ ! -z "$issues" ]; then
        echo "    Issues: $issues"
    fi
    echo ""
}

echo "🔍 Component Status Evaluation"
echo "=============================="
echo ""

# Check main documentation
echo -e "${BLUE}Documentation Status:${NC}"
if [ -f "README.md" ]; then
    echo "  ✅ Main README.md created"
else
    echo "  ❌ Main README.md missing"
fi

if [ -f "index.html" ]; then
    echo "  ✅ Main navigation dashboard created"
else
    echo "  ❌ Main navigation dashboard missing"
fi
echo ""

# Check each component
echo -e "${BLUE}Component Analysis:${NC}"
echo "==================="
echo ""

# WebScraper (Node.js)
check_node_component "WebScraper" "WebScraper"

# NotebookAI (React + FastAPI)
check_node_component "NotebookAI Frontend" "NotebookAI/frontend"
check_python_component "NotebookAI Backend" "NotebookAI/backend"

# NC Parser (Python)
check_python_component "NC Parser" "NC Parser"

# Machinist Game (Node.js)
check_node_component "Machinist Game" "machinist-runner-game"

# STEPViewer (C++/WASM)
check_component "STEPViewer" "STEPViewer" "step_viewer.wasm,StepViewerInterface.html"

# EVEMap (JavaScript)
check_component "EVEMap" "EVEMap" "eve_2d_prototype.html,eve_3d_prototype.html"

# Other components
check_component "MachineBooking" "MachineBooking" "MachineBooking.html"
check_component "BOB" "BOB" "BOB.html"
check_component "GimmeDaTools" "GimmeDaTools" "nc-tool-analyzer.html"

echo ""
echo -e "${GREEN}Summary & Recommendations:${NC}"
echo "==============================="
echo ""

echo "🎯 High Priority Actions:"
echo "  1. Set up dependencies for Python components (numpy, matplotlib, etc.)"
echo "  2. Run 'npm install' in Node.js components that need it"
echo "  3. Test WebScraper functionality (main feature)"
echo "  4. Verify NotebookAI Docker setup"
echo ""

echo "🔧 UI/UX Improvements Completed:"
echo "  ✅ Created main README.md with comprehensive documentation"
echo "  ✅ Built navigation dashboard (index.html)"
echo "  ✅ Identified all components and their status"
echo "  ✅ Documented quick start procedures"
echo ""

echo "📋 Next Phase Recommendations:"
echo "  1. Create standardized UI component library"
echo "  2. Add comprehensive testing across all components"
echo "  3. Implement Docker containerization for easier setup"
echo "  4. Create CI/CD pipeline for automated testing"
echo "  5. Add cross-component navigation links"
echo ""

echo "🚀 Ready to Use Components:"
echo "  • WebScraper - Full news aggregation platform"
echo "  • STEPViewer - 3D STEP file viewer (WASM ready)"
echo "  • EVEMap - Universe mapping tools"
echo "  • Static HTML components (BOB, MachineBooking, etc.)"
echo ""

echo -e "${GREEN}Evaluation Complete!${NC}"
echo "Use the main navigation dashboard (index.html) to access all tools."