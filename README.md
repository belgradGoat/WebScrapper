# WebScraper Multi-Tool Repository

A comprehensive collection of specialized applications and tools for news aggregation, AI analysis, 3D visualization, and game development.

## 🌟 Featured Applications

### 🗞️ WebScraper - News Aggregation Platform
**Status: ✅ Fully Functional**
- Multi-source news aggregation (GNews, Guardian, Reddit, Bluesky)
- AI-powered summarization using Gemma and Google Generative AI
- Real-time weather integration (US National Weather Service)
- Comprehensive web dashboard with social media feeds
- MongoDB integration for data persistence

**Quick Start:**
```bash
cd WebScraper
npm install
node server.js
# Visit: http://localhost:3000
```

### 🤖 NotebookAI - Multi-Modal AI Platform
**Status: ✅ Production Ready**
- Apple-inspired design with React 18 + TypeScript
- Multi-file data upload with AI analysis
- Real-time chat interface with context-aware responses
- Analytics dashboard and usage tracking
- FastAPI backend with PostgreSQL integration

**Quick Start:**
```bash
cd NotebookAI
# Backend
cd backend && pip install -r requirements.txt && uvicorn main:app --reload
# Frontend
cd frontend && npm install && npm start
```

### 🔧 NC Parser - G-code 3D Visualizer
**Status: ⚠️ Requires Dependencies**
- Parse NC files with G-code commands
- Generate 3D tool path visualizations
- Material removal simulation
- Multiple export formats (PLY, STL, OBJ)
- Interactive plotting with matplotlib/plotly

**Setup Required:**
```bash
cd "NC Parser"
pip install numpy matplotlib plotly pandas open3d
python main.py --create-sample
```

### 🎮 Machinist Runner Game
**Status: ✅ With Tests**
- Pac-Man inspired machinist-themed game
- Complete game engine with HTML5 Canvas
- Express.js backend with REST API
- Jest testing framework
- Live development server

**Quick Start:**
```bash
cd machinist-runner-game
npm install
npm start  # Runs both server and frontend
```

### 📐 STEPViewer - 3D CAD Viewer
**Status: ✅ Built**
- C++/WebAssembly 3D STEP file viewer
- Browser-based 3D rendering
- CMake build system with Emscripten
- Pre-built WASM modules included

**Usage:**
```bash
cd STEPViewer
# Open StepViewerInterface.html in browser
# WASM modules are pre-built and ready
```

### 🌌 EVEMap - Universe Mapping Tool
**Status: ✅ Functional**
- EVE Online universe visualization
- 2D and 3D prototype interfaces
- Market comparison tools
- API integration for real-time data
- Interactive region layouts

**Quick Start:**
```bash
cd EVEMap
npm install
# Open eve_2d_prototype.html or eve_3d_prototype.html
```

## 🚀 Quick Access Dashboard

### Core Applications
| Application | Port | Status | Quick Launch |
|-------------|------|--------|--------------|
| WebScraper | 3000 | ✅ Ready | `cd WebScraper && npm start` |
| NotebookAI Frontend | 3000 | ✅ Ready | `cd NotebookAI/frontend && npm start` |
| NotebookAI Backend | 8000 | ✅ Ready | `cd NotebookAI/backend && uvicorn main:app --reload` |
| Machinist Game | 8080 | ✅ Ready | `cd machinist-runner-game && npm start` |
| STEPViewer | File | ✅ Ready | Open `STEPViewer/StepViewerInterface.html` |
| EVEMap | File | ✅ Ready | Open `EVEMap/eve_2d_prototype.html` |

### Utility Tools
- **MachineBooking**: Machine scheduling interface
- **BOB**: Book of Becoming website
- **GimmeDaTools**: Various utility applications

## 🛠️ Development Setup

### Prerequisites
```bash
# Node.js applications
npm install

# Python applications  
pip install -r requirements.txt

# C++ applications (STEPViewer)
# Pre-built WASM files included
```

### Environment Variables
Create `.env` files where needed:
```bash
# WebScraper/.env
GEMINI_API_KEY=your_api_key_here
MONGODB_URI=your_mongodb_connection_string
```

## 📊 System Architecture

```
WebScraper Repository/
├── WebScraper/           # News aggregation platform (Node.js + Express)
├── NotebookAI/          # AI analysis platform (React + FastAPI)
├── NC Parser/           # G-code parser (Python + visualization)
├── machinist-runner-game/ # HTML5 game (JavaScript + Express)
├── STEPViewer/          # 3D CAD viewer (C++ + WebAssembly)
├── EVEMap/              # Universe mapping (JavaScript)
├── MachineBooking/      # Booking system (HTML/JS)
├── BOB/                 # Website (HTML/JS)
└── GimmeDaTools/        # Utilities
```

## 🧪 Testing

### Run All Tests
```bash
# Machinist Game (Jest)
cd machinist-runner-game && npm test

# WebScraper (Manual testing)
cd WebScraper && node server.js

# NotebookAI (Development mode)
cd NotebookAI && ./start.sh
```

## 📱 UI Systems

### Design Standards
- **WebScraper**: Modern responsive dashboard with glassmorphism
- **NotebookAI**: Apple-inspired design with React + Tailwind
- **Games**: Custom HTML5 Canvas interfaces
- **Viewers**: WebGL/WASM 3D interfaces

### Cross-Component Navigation
Each application runs independently but follows consistent:
- Port conventions (3000, 8000, 8080)
- File-based access for viewers
- Responsive design principles
- Modern JavaScript frameworks

## 🔧 Maintenance

### Component Health Check
```bash
# Check WebScraper
curl http://localhost:3000/health

# Check NotebookAI Backend
curl http://localhost:8000/docs

# Test Game API
curl http://localhost:8080/api/test
```

### Common Issues
1. **Port Conflicts**: Applications use standard ports (3000, 8000, 8080)
2. **Dependencies**: Python tools require numpy, matplotlib
3. **API Keys**: WebScraper needs valid API keys for full functionality
4. **CORS**: Some tools require same-origin access

## 📈 Roadmap

### Immediate Priorities
- [ ] Unified navigation dashboard
- [ ] Standardized UI components
- [ ] Comprehensive testing suite
- [ ] Docker containerization
- [ ] CI/CD pipeline

### Future Enhancements
- [ ] Single sign-on across applications
- [ ] Shared component library
- [ ] Mobile responsive improvements
- [ ] Real-time collaboration features
- [ ] Cloud deployment options

## 🤝 Contributing

1. **Choose a component** to work on
2. **Follow existing patterns** for UI and architecture
3. **Add tests** for new functionality
4. **Update documentation** for changes
5. **Test cross-component compatibility**

## 📄 License

Open source - Each component may have specific licensing terms.

---

**Quick Start Recommended Order:**
1. Start with **WebScraper** for full-featured experience
2. Try **NotebookAI** for AI capabilities
3. Explore **STEPViewer** for 3D visualization
4. Play **Machinist Game** for interactive demo
5. Check other tools as needed

**Need Help?** Check individual component README files for detailed setup instructions.