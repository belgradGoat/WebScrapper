# Machinist Runner

A Pac-Man inspired HTML5 game where you play as a machinist navigating a factory labyrinth to complete work orders while avoiding coworkers and managers.

## 🎮 Game Overview

Navigate through a factory maze completing work orders by visiting different stations:
- **🖥️ CAD Workstation** - Create CAD programs
- **📦 Material Room** - Collect materials  
- **⚙️ Machining Center** - Machine parts
- **🔍 Quality Control** - Pass quality inspections
- **🚚 Shipping** - Ship completed orders

## 🎯 Gameplay

### Basic Loop
1. Select a work order from the panel
2. Create a CAD program at the CAD workstation (spacebar mini-game)
3. Collect materials from the material room (spacebar mini-game)
4. Machine the part at the machining center (spacebar mini-game)
5. Pass quality control inspection (spacebar mini-game)
6. Ship the completed order

### 👥 Enemies
- **Coworkers** - Slow you down when encountered
- **Managers** - Pull you into meetings, causing longer delays  
- **HR** - Appears after missed deadlines, gives PIPs on contact

### 📈 Progression
- Complete orders to gain points and level up
- Higher levels bring more difficult orders and tighter deadlines
- Miss deadlines to get PIPs (Performance Improvement Plans)
- Game ends after 3 PIPs

## 🎮 Controls
- **WASD** or **Arrow Keys** - Move player
- **Spacebar** - Interact with stations (press multiple times for mini-games)
- **Mouse** - Click work orders to select them

## 🚀 Installation & Running

### Quick Start (Static Files)
```bash
# Navigate to project directory
cd machinist-runner-game

# Start a simple HTTP server
python3 -m http.server 8000

# Open browser to http://localhost:8000/src
```

### Full Server (with High Scores)
```bash
# Install dependencies
npm install

# Start the server
node server.js

# Open browser to http://localhost:3000
```

## ✨ Features

- ✅ Maze-based factory navigation
- ✅ Work order system with varying difficulty
- ✅ Multi-step manufacturing process
- ✅ Enemy AI (coworkers, managers, HR)
- ✅ Mini-games at each station
- ✅ Level progression system
- ✅ High score tracking (local + server)
- ✅ Sound effects with Web Audio API
- ✅ Responsive UI

## 🔧 Technical Details

- **Frontend**: HTML5 Canvas, JavaScript ES6
- **Backend**: Node.js + Express (optional, for high scores)
- **Storage**: Local Storage + JSON file persistence
- **Audio**: Web Audio API for sound effects

## 📁 File Structure
```
src/
├── index.html          # Main game page
├── css/
│   ├── styles.css      # Game styling
│   └── game.css        # Additional styles
└── js/
    ├── game.js         # Main game loop and rendering
    ├── player.js       # Player class and movement
    ├── enemies.js      # Enemy AI and behavior
    ├── stations.js     # Station definitions and interactions
    ├── workOrders.js   # Work order generation and management
    ├── gameState.js    # Game state management
    ├── utils.js        # Utility functions and UI
    └── sound.js        # Sound system
```

## 🛠️ Development

### Adding New Features
1. **New Station Types**: Add to `stations.js` and implement interaction logic
2. **New Enemy Types**: Extend `Enemy` class in `enemies.js`  
3. **New Work Order Types**: Modify `WorkOrder` class in `workOrders.js`

### Testing
```bash
npm test
```

### Deployment
The game can be deployed as static files to any web server or hosting service.

## 📄 License
MIT License - Feel free to modify and distribute!

## 🎯 Game Tips
- Plan your route efficiently between stations
- Watch the work order timers carefully
- Avoid dead ends when enemies are nearby
- Higher difficulty orders give more points
- Use sound cues to time your interactions
