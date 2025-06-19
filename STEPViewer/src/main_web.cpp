#include <iostream>
#include <string>
#include <vector>
#include <memory>
#include <cmath>
#include <fstream>
#include <sstream>

#ifdef __EMSCRIPTEN__
#include <emscripten.h>
#include <emscripten/html5.h>
#include <emscripten/bind.h>
#endif

// Simple 3D point and vector structures
struct Point3D {
    double x, y, z;
    Point3D(double x = 0, double y = 0, double z = 0) : x(x), y(y), z(z) {}
};

struct Vector3D {
    double x, y, z;
    Vector3D(double x = 0, double y = 0, double z = 0) : x(x), y(y), z(z) {}
    
    Vector3D cross(const Vector3D& other) const {
        return Vector3D(
            y * other.z - z * other.y,
            z * other.x - x * other.z,
            x * other.y - y * other.x
        );
    }
    
    double length() const {
        return std::sqrt(x * x + y * y + z * z);
    }
    
    Vector3D normalize() const {
        double len = length();
        if (len > 0) {
            return Vector3D(x / len, y / len, z / len);
        }
        return *this;
    }
};

struct BoundingBox {
    Point3D min, max;
    
    Point3D center() const {
        return Point3D(
            (min.x + max.x) / 2.0,
            (min.y + max.y) / 2.0,
            (min.z + max.z) / 2.0
        );
    }
    
    Vector3D dimensions() const {
        return Vector3D(
            max.x - min.x,
            max.y - min.y,
            max.z - min.z
        );
    }
};

struct UCS {
    Point3D origin;
    Vector3D xAxis, yAxis, zAxis;
    
    UCS() : xAxis(1, 0, 0), yAxis(0, 1, 0), zAxis(0, 0, 1) {}
};

// Simplified STEP processor for web
class STEPProcessorWeb {
private:
    std::string m_currentFile;
    bool m_fileLoaded = false;
    UCS m_ucs;
    BoundingBox m_boundingBox;
    std::vector<std::string> m_stepData;
    
public:
    STEPProcessorWeb() {
        std::cout << "STEPProcessorWeb initialized" << std::endl;
    }
    
    bool LoadSTEPFile(const std::string& filename) {
        std::cout << "Loading STEP file: " << filename << std::endl;
        
        m_currentFile = filename;
        m_stepData.clear();
        
#ifdef __EMSCRIPTEN__
        // Read file from Emscripten filesystem
        std::ifstream file(filename);
        if (!file.is_open()) {
            std::cerr << "Failed to open file: " << filename << std::endl;
            return false;
        }
        
        std::string line;
        while (std::getline(file, line)) {
            m_stepData.push_back(line);
        }
        file.close();
#endif
        
        // Parse basic STEP file structure
        if (ParseSTEPFile()) {
            m_fileLoaded = true;
            std::cout << "STEP file loaded successfully" << std::endl;
            std::cout << "Bounding box: (" 
                      << m_boundingBox.min.x << ", " << m_boundingBox.min.y << ", " << m_boundingBox.min.z 
                      << ") to (" 
                      << m_boundingBox.max.x << ", " << m_boundingBox.max.y << ", " << m_boundingBox.max.z 
                      << ")" << std::endl;
            return true;
        }
        
        return false;
    }
    
    void CreateUCS() {
        if (!m_fileLoaded) {
            std::cout << "No file loaded" << std::endl;
            return;
        }
        
        std::cout << "Creating UCS at part center..." << std::endl;
        
        // Set UCS origin to bounding box center
        m_ucs.origin = m_boundingBox.center();
        
        // Determine orientation based on longest dimension
        Vector3D dims = m_boundingBox.dimensions();
        
        if (dims.x >= dims.y && dims.x >= dims.z) {
            // X is longest - use it as Z axis
            m_ucs.zAxis = Vector3D(1, 0, 0);
            m_ucs.xAxis = Vector3D(0, 1, 0);
        } else if (dims.y >= dims.x && dims.y >= dims.z) {
            // Y is longest - use it as Z axis
            m_ucs.zAxis = Vector3D(0, 1, 0);
            m_ucs.xAxis = Vector3D(1, 0, 0);
        } else {
            // Z is longest - keep default orientation
            m_ucs.zAxis = Vector3D(0, 0, 1);
            m_ucs.xAxis = Vector3D(1, 0, 0);
        }
        
        // Calculate Y axis as cross product
        m_ucs.yAxis = m_ucs.zAxis.cross(m_ucs.xAxis).normalize();
        // Recalculate X to ensure orthogonality
        m_ucs.xAxis = m_ucs.yAxis.cross(m_ucs.zAxis).normalize();
        
        std::cout << "UCS created at center: (" 
                  << m_ucs.origin.x << ", " << m_ucs.origin.y << ", " << m_ucs.origin.z 
                  << ")" << std::endl;
        std::cout << "  X-axis: (" << m_ucs.xAxis.x << ", " << m_ucs.xAxis.y << ", " << m_ucs.xAxis.z << ")" << std::endl;
        std::cout << "  Y-axis: (" << m_ucs.yAxis.x << ", " << m_ucs.yAxis.y << ", " << m_ucs.yAxis.z << ")" << std::endl;
        std::cout << "  Z-axis: (" << m_ucs.zAxis.x << ", " << m_ucs.zAxis.y << ", " << m_ucs.zAxis.z << ")" << std::endl;
    }
    
    bool TakeScreenshot(const std::string& filename, int width = 800, int height = 600) {
        if (!m_fileLoaded) {
            std::cout << "No file loaded for screenshot" << std::endl;
            return false;
        }
        
        std::cout << "Taking screenshot: " << filename << " (" << width << "x" << height << ")" << std::endl;
        
#ifdef __EMSCRIPTEN__
        // Create a simple SVG representation of the bounding box and UCS
        std::ofstream file(filename);
        if (!file.is_open()) {
            return false;
        }
        
        // Generate SVG
        file << "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n";
        file << "<svg width=\"" << width << "\" height=\"" << height << "\" ";
        file << "xmlns=\"http://www.w3.org/2000/svg\">\n";
        
        // Background
        file << "<rect width=\"" << width << "\" height=\"" << height << "\" fill=\"#f0f0f0\"/>\n";
        
        // Title
        file << "<text x=\"" << width/2 << "\" y=\"30\" text-anchor=\"middle\" ";
        file << "font-family=\"Arial\" font-size=\"20\" font-weight=\"bold\">STEP File Visualization</text>\n";
        
        // Draw bounding box representation
        int boxX = width / 4;
        int boxY = height / 4;
        int boxW = width / 2;
        int boxH = height / 2;
        
        // Box outline
        file << "<rect x=\"" << boxX << "\" y=\"" << boxY << "\" ";
        file << "width=\"" << boxW << "\" height=\"" << boxH << "\" ";
        file << "fill=\"none\" stroke=\"#667eea\" stroke-width=\"2\"/>\n";
        
        // UCS axes at center
        int centerX = width / 2;
        int centerY = height / 2;
        int axisLen = 60;
        
        // X-axis (red)
        file << "<line x1=\"" << centerX << "\" y1=\"" << centerY << "\" ";
        file << "x2=\"" << centerX + axisLen << "\" y2=\"" << centerY << "\" ";
        file << "stroke=\"red\" stroke-width=\"3\"/>\n";
        file << "<text x=\"" << centerX + axisLen + 5 << "\" y=\"" << centerY + 5 << "\" ";
        file << "fill=\"red\" font-family=\"Arial\" font-size=\"14\">X</text>\n";
        
        // Y-axis (green)
        file << "<line x1=\"" << centerX << "\" y1=\"" << centerY << "\" ";
        file << "x2=\"" << centerX << "\" y2=\"" << centerY - axisLen << "\" ";
        file << "stroke=\"green\" stroke-width=\"3\"/>\n";
        file << "<text x=\"" << centerX + 5 << "\" y=\"" << centerY - axisLen - 5 << "\" ";
        file << "fill=\"green\" font-family=\"Arial\" font-size=\"14\">Y</text>\n";
        
        // Z-axis indicator (blue dot)
        file << "<circle cx=\"" << centerX << "\" cy=\"" << centerY << "\" r=\"5\" fill=\"blue\"/>\n";
        file << "<text x=\"" << centerX + 10 << "\" y=\"" << centerY - 10 << "\" ";
        file << "fill=\"blue\" font-family=\"Arial\" font-size=\"14\">Z</text>\n";
        
        // Info text
        file << "<text x=\"20\" y=\"" << height - 60 << "\" ";
        file << "font-family=\"Arial\" font-size=\"12\">File: " << m_currentFile << "</text>\n";
        
        file << "<text x=\"20\" y=\"" << height - 40 << "\" ";
        file << "font-family=\"Arial\" font-size=\"12\">Bounding Box Center: (";
        file << std::fixed << std::setprecision(2);
        file << m_ucs.origin.x << ", " << m_ucs.origin.y << ", " << m_ucs.origin.z << ")</text>\n";
        
        file << "<text x=\"20\" y=\"" << height - 20 << "\" ";
        file << "font-family=\"Arial\" font-size=\"12\">Dimensions: ";
        Vector3D dims = m_boundingBox.dimensions();
        file << dims.x << " x " << dims.y << " x " << dims.z << "</text>\n";
        
        file << "</svg>\n";
        file.close();
        
        std::cout << "Screenshot saved successfully (SVG format)" << std::endl;
        return true;
#else
        return false;
#endif
    }
    
    bool SaveSTEPCopy(const std::string& filename) {
        if (!m_fileLoaded) {
            std::cout << "No file loaded to copy" << std::endl;
            return false;
        }
        
        std::cout << "Saving STEP copy: " << filename << std::endl;
        
#ifdef __EMSCRIPTEN__
        std::ofstream file(filename);
        if (!file.is_open()) {
            return false;
        }
        
        // Write original STEP data with UCS information as comments
        file << "ISO-10303-21;\n";
        file << "HEADER;\n";
        file << "/* Original file: " << m_currentFile << " */\n";
        file << "/* UCS Origin: (" << m_ucs.origin.x << ", " << m_ucs.origin.y << ", " << m_ucs.origin.z << ") */\n";
        file << "/* UCS X-axis: (" << m_ucs.xAxis.x << ", " << m_ucs.xAxis.y << ", " << m_ucs.xAxis.z << ") */\n";
        file << "/* UCS Y-axis: (" << m_ucs.yAxis.x << ", " << m_ucs.yAxis.y << ", " << m_ucs.yAxis.z << ") */\n";
        file << "/* UCS Z-axis: (" << m_ucs.zAxis.x << ", " << m_ucs.zAxis.y << ", " << m_ucs.zAxis.z << ") */\n";
        
        // Write original STEP data
        for (const auto& line : m_stepData) {
            file << line << "\n";
        }
        
        file.close();
        
        std::cout << "STEP copy saved successfully with UCS information" << std::endl;
        return true;
#else
        return false;
#endif
    }
    
    // Getters for UI
    std::string GetUCSInfo() const {
        std::stringstream ss;
        ss << std::fixed << std::setprecision(3);
        ss << "Origin: (" << m_ucs.origin.x << ", " << m_ucs.origin.y << ", " << m_ucs.origin.z << ")";
        return ss.str();
    }
    
    std::string GetBoundingBoxInfo() const {
        std::stringstream ss;
        ss << std::fixed << std::setprecision(3);
        Vector3D dims = m_boundingBox.dimensions();
        ss << "Dimensions: " << dims.x << " x " << dims.y << " x " << dims.z;
        return ss.str();
    }
    
private:
    bool ParseSTEPFile() {
        // Simple STEP file parser to extract bounding box
        // In a real implementation, this would parse the actual geometry
        
        // For demo purposes, extract some basic info and create a dummy bounding box
        bool hasData = false;
        
        for (const auto& line : m_stepData) {
            if (line.find("CARTESIAN_POINT") != std::string::npos) {
                hasData = true;
                // In a real parser, we would extract actual coordinates
            }
        }
        
        // Create a dummy bounding box for demonstration
        if (hasData || !m_stepData.empty()) {
            m_boundingBox.min = Point3D(-50, -30, -20);
            m_boundingBox.max = Point3D(50, 30, 20);
            return true;
        }
        
        return false;
    }
};

// Global app instance
STEPProcessorWeb* g_processor = nullptr;

#ifdef __EMSCRIPTEN__
// C-style exports for JavaScript
extern "C" {
    EMSCRIPTEN_KEEPALIVE
    void initApp() {
        std::cout << "Initializing STEP Viewer..." << std::endl;
        if (g_processor) {
            delete g_processor;
        }
        g_processor = new STEPProcessorWeb();
        std::cout << "STEP Viewer initialized successfully" << std::endl;
    }
    
    EMSCRIPTEN_KEEPALIVE
    int loadSTEPFile(const char* filename) {
        if (!g_processor) {
            std::cerr << "Processor not initialized" << std::endl;
            return 0;
        }
        return g_processor->LoadSTEPFile(std::string(filename)) ? 1 : 0;
    }
    
    EMSCRIPTEN_KEEPALIVE
    void createUCS() {
        if (g_processor) {
            g_processor->CreateUCS();
        }
    }
    
    EMSCRIPTEN_KEEPALIVE
    int takeScreenshot(const char* filename, int width, int height) {
        if (!g_processor) return 0;
        return g_processor->TakeScreenshot(std::string(filename), width, height) ? 1 : 0;
    }
    
    EMSCRIPTEN_KEEPALIVE
    int saveSTEPCopy(const char* filename) {
        if (!g_processor) return 0;
        return g_processor->SaveSTEPCopy(std::string(filename)) ? 1 : 0;
    }
    
    EMSCRIPTEN_KEEPALIVE
    const char* getUCSInfo() {
        static std::string info;
        if (g_processor) {
            info = g_processor->GetUCSInfo();
            return info.c_str();
        }
        return "";
    }
    
    EMSCRIPTEN_KEEPALIVE
    const char* getBoundingBoxInfo() {
        static std::string info;
        if (g_processor) {
            info = g_processor->GetBoundingBoxInfo();
            return info.c_str();
        }
        return "";
    }
}
#endif

int main() {
    std::cout << "STEP Viewer Web Module" << std::endl;
    return 0;
}