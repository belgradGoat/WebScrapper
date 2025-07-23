# WebScraper Multi-Tool Repository - Technical Implementation Guide

## 🏗️ Architecture Overview

This repository implements a microservices-style architecture with multiple specialized applications, each optimized for specific use cases while maintaining consistent UI/UX patterns.

## 🔧 Technology Stack Summary

### Frontend Technologies
```
React 18 + TypeScript    → NotebookAI (modern SPA)
HTML5 + Vanilla JS       → WebScraper, Games, Viewers
WebAssembly + C++         → STEPViewer (3D rendering)
WebGL + JavaScript       → EVEMap (3D visualization)
```

### Backend Technologies
```
Node.js + Express        → WebScraper, Game servers
FastAPI + Python         → NotebookAI backend
Python CLI               → NC Parser, data processing
Static File Serving      → Multiple components
```

### Database & Storage
```
MongoDB                  → WebScraper (news data, summaries)
PostgreSQL + Redis       → NotebookAI (user data, caching)
SQLite                   → Local data storage
File System              → Configuration, exports
```

### External Integrations
```
AI/ML APIs               → Google Generative AI, Gemma
News APIs                → GNews, Guardian, Google News RSS
Social Media             → Reddit, Bluesky
Weather Service          → US National Weather Service
3D Graphics              → Three.js, WebGL, Open3D
```

## 🚀 Quick Start Commands

### WebScraper (Main Application)
```bash
cd WebScraper
npm install                # Install dependencies
node server.js            # Start server on :3000
# Access: http://localhost:3000
```

### NotebookAI (AI Platform)
```bash
cd NotebookAI
# Backend
cd backend && pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend  
cd frontend && npm install && npm start
# Access: http://localhost:3000 (frontend), :8000 (API)
```

### Machinist Game
```bash
cd machinist-runner-game
npm install
npm start                  # Starts both server and live reload
# Access: http://localhost:8080
```

### NC Parser (Dependencies Required)
```bash
cd "NC Parser"
pip install numpy matplotlib plotly pandas open3d
python main.py --help     # See usage options
python main.py --create-sample  # Test with sample file
```

### File-Based Applications
```bash
# Serve via HTTP server for cross-origin access
python -m http.server 8080

# Then access:
# http://localhost:8080/STEPViewer/StepViewerInterface.html
# http://localhost:8080/EVEMap/eve_2d_prototype.html
# http://localhost:8080/MachineBooking/MachineBooking.html
```

## 📊 Component Details

### WebScraper - Eagle Watchtower
**Purpose**: Comprehensive news aggregation and AI analysis platform
```javascript
// Key features implemented:
- Multi-source news scraping (4+ APIs)
- AI summarization with Gemma and Google AI
- Real-time social media feeds (Reddit, Bluesky)
- Weather service integration
- MongoDB data persistence
- Responsive dashboard UI with glassmorphism
```

### NotebookAI
**Purpose**: Multi-modal AI data analysis platform
```python
# Architecture:
Frontend: React + TypeScript + Tailwind CSS
Backend: FastAPI + PostgreSQL + Redis
Features: File upload, AI chat, analytics dashboard
Design: Apple-inspired with glassmorphism effects
```

### STEPViewer
**Purpose**: 3D CAD file visualization in browser
```cpp
// Implementation:
Core: C++ with STEP file parsing
Rendering: WebAssembly + Three.js
Features: 3D navigation, measurement tools, export
Format: Pre-compiled WASM modules included
```

### NC Parser
**Purpose**: G-code analysis with 3D visualization
```python
# Capabilities:
- G-code parsing (G00, G01, G02, G03, M-codes)
- Tool path calculation and interpolation
- 3D point cloud generation
- Material removal simulation
- Export to PLY, STL, OBJ formats
```

### EVEMap
**Purpose**: EVE Online universe mapping and visualization
```javascript
// Features:
- 2D and 3D universe visualization
- Market comparison tools
- Real-time API data integration
- Interactive region navigation
```

## 🎨 UI/UX Implementation

### Design System
```css
/* Color Palette */
Primary: linear-gradient(135deg, #667eea 0%, #764ba2 100%)
Secondary: rgba(255, 255, 255, 0.95)
Accent: #28a745, #17a2b8, #ffc107

/* Typography */
Font: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto'
Headers: 2.5em with text-shadow
Body: 1em with 1.6 line-height

/* Effects */
Glassmorphism: backdrop-filter: blur(10px)
Shadows: 0 8px 32px rgba(0,0,0,0.1)
Transitions: all 0.3s ease
```

### Responsive Breakpoints
```css
Mobile: max-width: 768px (single column layout)
Tablet: 768px - 1200px (two column grid)
Desktop: 1200px+ (three+ column grid)
```

### Component Patterns
```html
<!-- Card Pattern -->
<div class="app-card">
  <div class="app-header">
    <div class="app-icon">🔧</div>
    <div class="app-title">Component Name</div>
    <div class="app-status status-ready">✅ Ready</div>
  </div>
  <div class="app-description">...</div>
  <div class="app-actions">
    <button class="btn btn-primary">Launch</button>
  </div>
</div>
```

## 🔐 Security & Configuration

### Environment Variables Required
```bash
# WebScraper (.env)
GEMINI_API_KEY=your_gemini_api_key
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/db

# NotebookAI Backend (.env)
DATABASE_URL=postgresql://user:pass@localhost/notebookai
REDIS_URL=redis://localhost:6379
OPENAI_API_KEY=your_openai_key
```

### API Keys & External Services
```
GNews API: dac11b1cf0731071bb89fbfca20fbadf (included)
Guardian API: f66ca23b-5fd8-4869-9aff-6256719af4ce (included)
Google Gemini: User-provided required for AI features
MongoDB Atlas: Connection string required
```

## 🧪 Testing Strategy

### Implemented Tests
```bash
# Machinist Game
cd machinist-runner-game
npm test                   # Jest test suite

# WebScraper
node server.js            # Manual testing via dashboard
curl http://localhost:3000/health  # Health endpoint

# NC Parser
python main.py --create-sample    # Test with sample data
```

### Testing Gaps & Recommendations
1. **Unit Tests**: Add for WebScraper API endpoints
2. **Integration Tests**: Cross-component communication
3. **E2E Tests**: Complete user workflows
4. **Performance Tests**: Load testing for concurrent users

## 🚀 Deployment Options

### Local Development
```bash
# Start all services
./start_all_services.sh   # Custom script to start major components
```

### Docker Deployment (NotebookAI)
```bash
cd NotebookAI
docker-compose up -d      # Full stack with database
```

### Production Considerations
```
Load Balancer: Nginx for static files and reverse proxy
SSL: Let's Encrypt certificates for HTTPS
Monitoring: Health endpoints implemented
Scaling: Each component can scale independently
```

## 📋 Development Workflow

### Adding New Components
1. Create component directory with clear naming
2. Include package.json (Node.js) or requirements.txt (Python)
3. Add README.md with setup instructions
4. Update main navigation dashboard
5. Add to component evaluation script
6. Document in main README.md

### UI Component Standards
1. Follow glassmorphism design patterns
2. Use consistent color palette and typography
3. Implement responsive grid layouts
4. Add proper accessibility attributes
5. Include loading states and error handling

### Code Quality
```bash
# Linting (where configured)
npm run lint              # ESLint for JavaScript
black .                   # Python code formatting
prettier --write .        # Code formatting

# Documentation
# Each component requires README.md
# API endpoints documented inline
# Complex algorithms explained with comments
```

## 🔄 Maintenance & Updates

### Regular Tasks
```bash
# Security updates
npm audit fix             # Node.js dependencies
pip-review --auto         # Python package updates

# Performance monitoring
# Check server logs for errors
# Monitor API rate limits
# Verify external service availability
```

### Version Management
```
Components versioned independently
Major version changes documented in CHANGELOG.md
Breaking changes communicated via README updates
```

---

**Technical Lead**: System evaluation and documentation complete  
**Next Review**: Monthly architecture review recommended  
**Support**: Check individual component README files for specific issues