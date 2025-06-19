#include <iostream>
#include <string>
#include <vector>
#include <memory>
#include <cmath>
#include <fstream>
#include <sstream>
#include <algorithm>
#include <unordered_map>
#include <iomanip>

#ifdef __EMSCRIPTEN__
#include <emscripten.h>
#include <emscripten/html5.h>
#include <emscripten/bind.h>
#endif

// Simple 3D point and vector structures
struct Point3D {
    double x, y, z;
    Point3D(double x = 0, double y = 0, double z = 0) : x(x), y(y), z(z) {}
    
    Point3D operator+(const Point3D& other) const {
        return Point3D(x + other.x, y + other.y, z + other.z);
    }
    
    Point3D operator-(const Point3D& other) const {
        return Point3D(x - other.x, y - other.y, z - other.z);
    }
    
    Point3D operator*(double scalar) const {
        return Point3D(x * scalar, y * scalar, z * scalar);
    }
};

struct Vector3D {
    double x, y, z;
    Vector3D(double x = 0, double y = 0, double z = 0) : x(x), y(y), z(z) {}
    
    Vector3D(const Point3D& p1, const Point3D& p2) 
        : x(p2.x - p1.x), y(p2.y - p1.y), z(p2.z - p1.z) {}
    
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
    
    BoundingBox() : min(1e9, 1e9, 1e9), max(-1e9, -1e9, -1e9) {}
    
    void expand(const Point3D& point) {
        min.x = std::min(min.x, point.x);
        min.y = std::min(min.y, point.y);
        min.z = std::min(min.z, point.z);
        max.x = std::max(max.x, point.x);
        max.y = std::max(max.y, point.y);
        max.z = std::max(max.z, point.z);
    }
    
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

// Mesh data structure
struct MeshData {
    std::vector<float> vertices;    // x,y,z, x,y,z, ...
    std::vector<float> normals;     // nx,ny,nz, nx,ny,nz, ...
    std::vector<uint32_t> indices;  // triangle indices
    
    void clear() {
        vertices.clear();
        normals.clear();
        indices.clear();
    }
    
    void addTriangle(const Point3D& p1, const Point3D& p2, const Point3D& p3) {
        // Calculate normal
        Vector3D v1(p1, p2);
        Vector3D v2(p1, p3);
        Vector3D normal = v1.cross(v2).normalize();
        
        // Store vertex indices
        uint32_t startIdx = vertices.size() / 3;
        
        // Add vertices
        vertices.push_back(p1.x); vertices.push_back(p1.y); vertices.push_back(p1.z);
        vertices.push_back(p2.x); vertices.push_back(p2.y); vertices.push_back(p2.z);
        vertices.push_back(p3.x); vertices.push_back(p3.y); vertices.push_back(p3.z);
        
        // Add normals (same for all vertices of the triangle)
        for (int i = 0; i < 3; i++) {
            normals.push_back(normal.x);
            normals.push_back(normal.y);
            normals.push_back(normal.z);
        }
        
        // Add indices
        indices.push_back(startIdx);
        indices.push_back(startIdx + 1);
        indices.push_back(startIdx + 2);
    }
    
    void addQuad(const Point3D& p1, const Point3D& p2, const Point3D& p3, const Point3D& p4) {
        // Split quad into two triangles
        addTriangle(p1, p2, p3);
        addTriangle(p1, p3, p4);
    }
};

// Simple STEP entity parser - using struct instead of class to avoid constructor issues
struct STEPEntity {
    int id = 0;
    std::string type;
    std::string data;
    
    STEPEntity() = default;
    STEPEntity(int id, const std::string& type, const std::string& data) 
        : id(id), type(type), data(data) {}
};

// Simplified STEP processor for web
class STEPProcessorWeb {
private:
    std::string m_currentFile;
    bool m_fileLoaded = false;
    UCS m_ucs;
    BoundingBox m_boundingBox;
    std::vector<std::string> m_stepData;
    MeshData m_mesh;
    std::unordered_map<int, STEPEntity> m_entities;
    
public:
    STEPProcessorWeb() {
        std::cout << "STEPProcessorWeb initialized" << std::endl;
    }
    
    bool LoadSTEPFile(const std::string& filename) {
        std::cout << "Loading STEP file: " << filename << std::endl;
        
        m_currentFile = filename;
        m_stepData.clear();
        m_entities.clear();
        m_mesh.clear();
        m_boundingBox = BoundingBox();
        
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
        
        // Parse STEP file and extract mesh
        if (ParseSTEPFile() && ExtractMesh()) {
            m_fileLoaded = true;
            std::cout << "STEP file loaded successfully" << std::endl;
            std::cout << "Mesh statistics: " << std::endl;
            std::cout << "  Vertices: " << m_mesh.vertices.size() / 3 << std::endl;
            std::cout << "  Triangles: " << m_mesh.indices.size() / 3 << std::endl;
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
    }
    
    // Mesh data accessors for JavaScript
    size_t GetVertexCount() const {
        return m_mesh.vertices.size();
    }
    
    size_t GetNormalCount() const {
        return m_mesh.normals.size();
    }
    
    size_t GetIndexCount() const {
        return m_mesh.indices.size();
    }
    
    const float* GetVertices() const {
        return m_mesh.vertices.data();
    }
    
    const float* GetNormals() const {
        return m_mesh.normals.data();
    }
    
    const uint32_t* GetIndices() const {
        return m_mesh.indices.data();
    }
    
    bool TakeScreenshot(const std::string& filename, int width = 800, int height = 600) {
        // Keep existing screenshot functionality
        if (!m_fileLoaded) {
            std::cout << "No file loaded for screenshot" << std::endl;
            return false;
        }
        
        std::cout << "Taking screenshot: " << filename << " (" << width << "x" << height << ")" << std::endl;
        
#ifdef __EMSCRIPTEN__
        // Create a simple SVG representation
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
        
        // Add mesh info
        file << "<text x=\"20\" y=\"" << height - 80 << "\" ";
        file << "font-family=\"Arial\" font-size=\"12\">Mesh: " 
             << m_mesh.vertices.size() / 3 << " vertices, "
             << m_mesh.indices.size() / 3 << " triangles</text>\n";
        
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
        file << "ENDSEC;\n";
        
        // Write original STEP data (skip original header if present)
        bool inHeader = false;
        for (const auto& line : m_stepData) {
            if (line.find("HEADER;") != std::string::npos) {
                inHeader = true;
                continue;
            }
            if (inHeader && line.find("ENDSEC;") != std::string::npos) {
                inHeader = false;
                continue;
            }
            if (!inHeader) {
                file << line << "\n";
            }
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
    Point3D ParseCartesianPoint(const std::string& data) {
        // Parse CARTESIAN_POINT data like ('', (10.0, 20.0, 30.0))
        Point3D point;
        size_t start = data.find('(');
        size_t end = data.rfind(')');
        if (start != std::string::npos && end != std::string::npos) {
            start = data.find('(', start + 1); // Find second '('
            if (start != std::string::npos) {
                std::string coords = data.substr(start + 1, end - start - 1);
                std::stringstream ss(coords);
                char comma;
                ss >> point.x >> comma >> point.y >> comma >> point.z;
            }
        }
        return point;
    }
    
    std::vector<int> ParseRefs(const std::string& data) {
        // Parse references like (#123, #456, #789)
        std::vector<int> refs;
        size_t pos = 0;
        while ((pos = data.find('#', pos)) != std::string::npos) {
            int ref = 0;
            sscanf(data.c_str() + pos + 1, "%d", &ref);
            refs.push_back(ref);
            pos++;
        }
        return refs;
    }
    
    bool ParseSTEPFile() {
        // Parse STEP entities
        bool inData = false;
        std::string currentEntity;
        
        for (const auto& line : m_stepData) {
            if (line.find("DATA;") != std::string::npos) {
                inData = true;
                continue;
            }
            if (line.find("ENDSEC;") != std::string::npos) {
                inData = false;
                continue;
            }
            
            if (inData) {
                currentEntity += line;
                
                // Check if entity is complete
                if (line.find(';') != std::string::npos) {
                    // Parse entity
                    size_t idPos = currentEntity.find('#');
                    size_t equalPos = currentEntity.find('=');
                    size_t typeEndPos = currentEntity.find('(');
                    
                    if (idPos != std::string::npos && equalPos != std::string::npos && typeEndPos != std::string::npos) {
                        int id = 0;
                        sscanf(currentEntity.c_str() + idPos + 1, "%d", &id);
                        
                        std::string type = currentEntity.substr(equalPos + 1, typeEndPos - equalPos - 1);
                        // Remove spaces
                        type.erase(std::remove_if(type.begin(), type.end(), ::isspace), type.end());
                        
                        std::string data = currentEntity.substr(typeEndPos);
                        
                        // Use emplace instead of operator[] to avoid default construction
                        m_entities.emplace(id, STEPEntity(id, type, data));
                    }
                    
                    currentEntity.clear();
                }
            }
        }
        
        return !m_entities.empty();
    }
    
    bool ExtractMesh() {
        // For demonstration, create a simple box mesh if we have any entities
        // In a real implementation, you would parse the actual geometry
        
        if (m_entities.empty()) {
            // Create default box
            CreateBoxMesh(100, 60, 40);
            return true;
        }
        
        // Look for specific entity types and extract geometry
        bool meshCreated = false;
        
        for (const auto& [id, entity] : m_entities) {
            if (entity.type == "CARTESIAN_POINT") {
                Point3D point = ParseCartesianPoint(entity.data);
                m_boundingBox.expand(point);
            }
            // Add more entity type handlers here
            // For now, we'll create a simple mesh based on bounding box
        }
        
        // If we found points, create a box mesh based on bounding box
        if (m_boundingBox.min.x < m_boundingBox.max.x) {
            Vector3D dims = m_boundingBox.dimensions();
            CreateBoxMesh(dims.x, dims.y, dims.z);
            meshCreated = true;
        } else {
            // Create default box
            CreateBoxMesh(100, 60, 40);
            meshCreated = true;
        }
        
        return meshCreated;
    }
    
    void CreateBoxMesh(double width, double height, double depth) {
        // Create a simple box mesh centered at origin
        double hw = width / 2.0;
        double hh = height / 2.0;
        double hd = depth / 2.0;
        
        // Define 8 vertices of the box
        Point3D vertices[8] = {
            Point3D(-hw, -hh, -hd), // 0: left bottom back
            Point3D( hw, -hh, -hd), // 1: right bottom back
            Point3D( hw,  hh, -hd), // 2: right top back
            Point3D(-hw,  hh, -hd), // 3: left top back
            Point3D(-hw, -hh,  hd), // 4: left bottom front
            Point3D( hw, -hh,  hd), // 5: right bottom front
            Point3D( hw,  hh,  hd), // 6: right top front
            Point3D(-hw,  hh,  hd)  // 7: left top front
        };
        
        // Update bounding box
        for (const auto& v : vertices) {
            m_boundingBox.expand(v);
        }
        
        // Create faces (2 triangles per face, 6 faces total)
        // Front face
        m_mesh.addQuad(vertices[4], vertices[5], vertices[6], vertices[7]);
        // Back face
        m_mesh.addQuad(vertices[1], vertices[0], vertices[3], vertices[2]);
        // Top face
        m_mesh.addQuad(vertices[7], vertices[6], vertices[2], vertices[3]);
        // Bottom face
        m_mesh.addQuad(vertices[0], vertices[1], vertices[5], vertices[4]);
        // Right face
        m_mesh.addQuad(vertices[5], vertices[1], vertices[2], vertices[6]);
        // Left face
        m_mesh.addQuad(vertices[0], vertices[4], vertices[7], vertices[3]);
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
    
    // Mesh data access functions
    EMSCRIPTEN_KEEPALIVE
    int getVertexCount() {
        if (!g_processor) return 0;
        return g_processor->GetVertexCount();
    }
    
    EMSCRIPTEN_KEEPALIVE
    int getNormalCount() {
        if (!g_processor) return 0;
        return g_processor->GetNormalCount();
    }
    
    EMSCRIPTEN_KEEPALIVE
    int getIndexCount() {
        if (!g_processor) return 0;
        return g_processor->GetIndexCount();
    }
    
    EMSCRIPTEN_KEEPALIVE
    float* getVertices() {
        if (!g_processor) return nullptr;
        return const_cast<float*>(g_processor->GetVertices());
    }
    
    EMSCRIPTEN_KEEPALIVE
    float* getNormals() {
        if (!g_processor) return nullptr;
        return const_cast<float*>(g_processor->GetNormals());
    }
    
    EMSCRIPTEN_KEEPALIVE
    uint32_t* getIndices() {
        if (!g_processor) return nullptr;
        return const_cast<uint32_t*>(g_processor->GetIndices());
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