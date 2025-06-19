#include <STEPCAFControl_Reader.hxx>
#include <TDocStd_Document.hxx>
#include <TDocStd_Application.hxx>
#include <XCAFDoc_DocumentTool.hxx>
#include <XCAFDoc_ShapeTool.hxx>
#include <TopoDS_Shape.hxx>
#include <Bnd_Box.hxx>
#include <BRepBndLib.hxx>
#include <gp_Pnt.hxx>
#include <gp_Dir.hxx>
#include <gp_Ax3.hxx>
#include <V3d_View.hxx>
#include <V3d_Viewer.hxx>
#include <AIS_InteractiveContext.hxx>
#include <AIS_Shape.hxx>
#include <OpenGl_GraphicDriver.hxx>
#include <Aspect_DisplayConnection.hxx>
#include <Image_AlienPixMap.hxx>
#include <STEPControl_Writer.hxx>
#include <BRepTools.hxx>
#include <TopExp_Explorer.hxx>
#include <TopoDS.hxx>
#include <BRep_Tool.hxx>
#include <GeomLProp_SLProps.hxx>
#include <GeomAdaptor_Surface.hxx>
#include <Precision.hxx>
#include <TDF_LabelSequence.hxx>
#include <IFSelect_ReturnStatus.hxx>

#include <iostream>
#include <string>
#include <algorithm>
#include <vector>
#include <memory>

#ifdef __EMSCRIPTEN__
#include <emscripten.h>
#include <emscripten/html5.h>
#endif

class STEPProcessor {
private:
    Handle(TDocStd_Document) m_document;
    Handle(V3d_Viewer) m_viewer;
    Handle(V3d_View) m_view;
    Handle(AIS_InteractiveContext) m_context;
    TopoDS_Shape m_shape;
    gp_Ax3 m_ucs;
    
public:
    STEPProcessor() {
        // Initialize OCCT document
        Handle(TDocStd_Application) app = new TDocStd_Application();
        app->NewDocument("MDTV-XCAF", m_document);
        
        // Initialize 3D viewer
        Handle(Aspect_DisplayConnection) displayConnection = new Aspect_DisplayConnection();
        Handle(OpenGl_GraphicDriver) graphicDriver = new OpenGl_GraphicDriver(displayConnection);
        
        m_viewer = new V3d_Viewer(graphicDriver);
        m_viewer->SetDefaultLights();
        m_viewer->SetLightOn();
        
        m_view = m_viewer->CreateView();
        m_context = new AIS_InteractiveContext(m_viewer);
    }
    
    bool LoadSTEPFile(const std::string& filename) {
        STEPCAFControl_Reader reader;
        
        // Read STEP file
        IFSelect_ReturnStatus status = reader.ReadFile(filename.c_str());
        if (status != IFSelect_RetDone) {
            std::cerr << "Error reading STEP file: " << filename << std::endl;
            return false;
        }
        
        // Transfer to document
        if (!reader.Transfer(m_document)) {
            std::cerr << "Error transferring STEP data to document" << std::endl;
            return false;
        }
        
        // Get the shape
        Handle(XCAFDoc_ShapeTool) shapeTool = XCAFDoc_DocumentTool::ShapeTool(m_document->Main());
        TDF_LabelSequence labels;
        shapeTool->GetFreeShapes(labels);
        
        if (labels.Length() == 0) {
            std::cerr << "No shapes found in STEP file" << std::endl;
            return false;
        }
        
        // Get the first shape (you might want to handle multiple shapes differently)
        TopoDS_Shape shape = shapeTool->GetShape(labels.Value(1));
        if (shape.IsNull()) {
            std::cerr << "Invalid shape found" << std::endl;
            return false;
        }
        
        m_shape = shape;
        
        // Display the shape
        Handle(AIS_Shape) aisShape = new AIS_Shape(m_shape);
        m_context->Display(aisShape, Standard_True);
        
        return true;
    }
    
    void CreateUCS() {
        if (m_shape.IsNull()) {
            std::cerr << "No shape loaded" << std::endl;
            return;
        }
        
        // Calculate bounding box
        Bnd_Box boundingBox;
        BRepBndLib::Add(m_shape, boundingBox);
        
        if (boundingBox.IsVoid()) {
            std::cerr << "Invalid bounding box" << std::endl;
            return;
        }
        
        Standard_Real xMin, yMin, zMin, xMax, yMax, zMax;
        boundingBox.Get(xMin, yMin, zMin, xMax, yMax, zMax);
        
        // Calculate center point
        gp_Pnt center((xMin + xMax) / 2.0, (yMin + yMax) / 2.0, (zMin + zMax) / 2.0);
        
        // Calculate dimensions
        Standard_Real xDim = xMax - xMin;
        Standard_Real yDim = yMax - yMin;
        Standard_Real zDim = zMax - zMin;
        
        // Determine longest edge direction
        gp_Dir zDirection;
        if (xDim >= yDim && xDim >= zDim) {
            // X is longest
            zDirection = gp_Dir(1, 0, 0);
        } else if (yDim >= xDim && yDim >= zDim) {
            // Y is longest
            zDirection = gp_Dir(0, 1, 0);
        } else {
            // Z is longest
            zDirection = gp_Dir(0, 0, 1);
        }
        
        // Create UCS
        gp_Dir xDirection(1, 0, 0);
        if (zDirection.IsParallel(xDirection, Precision::Angular())) {
            xDirection = gp_Dir(0, 1, 0);
        }
        
        gp_Dir yDirection = zDirection.Crossed(xDirection);
        xDirection = yDirection.Crossed(zDirection);
        
        m_ucs = gp_Ax3(center, zDirection, xDirection);
        
        std::cout << "UCS created at center: (" 
                  << center.X() << ", " << center.Y() << ", " << center.Z() 
                  << ") with Z direction: (" 
                  << zDirection.X() << ", " << zDirection.Y() << ", " << zDirection.Z() 
                  << ")" << std::endl;
    }
    
    bool TakeScreenshot(const std::string& filename, int width = 800, int height = 600) {
        if (m_view.IsNull()) {
            std::cerr << "No view available for screenshot" << std::endl;
            return false;
        }
        
        // Fit all objects in view and redraw
        m_view->FitAll();
        m_view->Redraw();
        
        // Create image with specified dimensions
        Image_AlienPixMap image;
        if (!m_view->ToPixMap(image, width, height)) {
            std::cerr << "Failed to capture view to image" << std::endl;
            return false;
        }
        
        // Save image
        if (!image.Save(filename.c_str())) {
            std::cerr << "Failed to save image: " << filename << std::endl;
            return false;
        }
        
        std::cout << "Screenshot saved: " << filename << std::endl;
        return true;
    }
    
    bool SaveSTEPCopy(const std::string& filename) {
        if (m_shape.IsNull()) {
            std::cerr << "No shape to save" << std::endl;
            return false;
        }
        
        STEPControl_Writer writer;
        IFSelect_ReturnStatus status = writer.Transfer(m_shape, STEPControl_AsIs);
        
        if (status != IFSelect_RetDone) {
            std::cerr << "Error transferring shape for writing" << std::endl;
            return false;
        }
        
        status = writer.Write(filename.c_str());
        if (status != IFSelect_RetDone) {
            std::cerr << "Error writing STEP file: " << filename << std::endl;
            return false;
        }
        
        std::cout << "STEP file saved: " << filename << std::endl;
        return true;
    }
    
    gp_Ax3 GetUCS() const {
        return m_ucs;
    }
    
    void SetViewDirection(const gp_Dir& direction) {
        if (!m_view.IsNull()) {
            // Use correct API for setting view direction
            m_view->SetProj(direction.X(), direction.Y(), direction.Z());
            m_view->FitAll();
        }
    }
    
    void SetIsometricView() {
        if (!m_view.IsNull()) {
            m_view->SetProj(V3d_XposYnegZpos);
            m_view->FitAll();
        }
    }
};

// Main application class
class STEPViewerApp {
private:
    std::unique_ptr<STEPProcessor> m_processor;
    
public:
    STEPViewerApp() : m_processor(std::make_unique<STEPProcessor>()) {}
    
    bool ProcessFile(const std::string& inputFile, 
                    const std::string& outputImageFile = "",
                    const std::string& outputSTEPFile = "") {
        
        // Load STEP file
        if (!m_processor->LoadSTEPFile(inputFile)) {
            return false;
        }
        
        // Create UCS
        m_processor->CreateUCS();
        
        // Set isometric view for better visualization
        m_processor->SetIsometricView();
        
        // Take screenshot if requested
        if (!outputImageFile.empty()) {
            if (!m_processor->TakeScreenshot(outputImageFile)) {
                std::cerr << "Failed to save screenshot" << std::endl;
            }
        }
        
        // Save STEP copy if requested
        if (!outputSTEPFile.empty()) {
            if (!m_processor->SaveSTEPCopy(outputSTEPFile)) {
                std::cerr << "Failed to save STEP copy" << std::endl;
            }
        }
        
        return true;
    }
    
    STEPProcessor* GetProcessor() {
        return m_processor.get();
    }
};

// Global app instance for Emscripten
STEPViewerApp* g_app = nullptr;

#ifdef __EMSCRIPTEN__
// Emscripten bindings for web usage
extern "C" {
    EMSCRIPTEN_KEEPALIVE
    void initApp() {
        g_app = new STEPViewerApp();
    }
    
    EMSCRIPTEN_KEEPALIVE
    int loadSTEPFile(const char* filename) {
        if (!g_app) return 0;
        return g_app->GetProcessor()->LoadSTEPFile(std::string(filename)) ? 1 : 0;
    }
    
    EMSCRIPTEN_KEEPALIVE
    void createUCS() {
        if (g_app) {
            g_app->GetProcessor()->CreateUCS();
        }
    }
    
    EMSCRIPTEN_KEEPALIVE
    int takeScreenshot(const char* filename, int width, int height) {
        if (!g_app) return 0;
        return g_app->GetProcessor()->TakeScreenshot(std::string(filename), width, height) ? 1 : 0;
    }
    
    EMSCRIPTEN_KEEPALIVE
    int saveSTEPCopy(const char* filename) {
        if (!g_app) return 0;
        return g_app->GetProcessor()->SaveSTEPCopy(std::string(filename)) ? 1 : 0;
    }
}
#endif

// Main function for desktop usage
#ifndef __EMSCRIPTEN__
int main(int argc, char* argv[]) {
    if (argc < 2) {
        std::cout << "Usage: " << argv[0] << " <input.step> [output_image.png] [output_copy.step]" << std::endl;
        return 1;
    }
    
    std::string inputFile = argv[1];
    std::string outputImageFile = (argc > 2) ? argv[2] : inputFile + "_screenshot.png";
    std::string outputSTEPFile = (argc > 3) ? argv[3] : inputFile + "_copy.step";
    
    STEPViewerApp app;
    
    if (!app.ProcessFile(inputFile, outputImageFile, outputSTEPFile)) {
        std::cerr << "Failed to process file: " << inputFile << std::endl;
        return 1;
    }
    
    std::cout << "Processing completed successfully!" << std::endl;
    return 0;
}
#endif