# Game Design Document for Machinist Runner Game

## Game Overview
Machinist Runner is an HTML5 and JavaScript game inspired by classic arcade games like Pac-Man. Players take on the role of a machinist navigating a labyrinthine factory while completing work orders and avoiding coworkers and managers. The game combines elements of strategy, resource management, and fast-paced action.

## Gameplay Mechanics
- **Player Movement**: The player can navigate through the maze using keyboard controls (arrow keys or WASD).
- **Work Orders**: Players will receive work orders that require them to complete tasks at various stations. Each order has a difficulty level and specific requirements.
- **Stations**: The game features several stations:
  - **CAD Workstation**: Create CAD programs.
  - **Material Room**: Collect necessary materials for work orders.
  - **Machining Center**: Machine parts using collected materials.
  - **Quality Control (QC)**: Pass quality checks to ensure parts meet standards.
  - **Shipping**: Ship completed orders for points.
  
## Objectives
- Complete as many work orders as possible within a time limit.
- Avoid being caught by coworkers and managers, which will slow down the player.
- Accumulate points by completing orders and progressing through levels.

## Scoring System
- Points are awarded based on the difficulty of the work orders completed.
- Bonus points for completing multiple orders in a row without being caught.
- Penalties for failing quality control checks or missing deadlines.

## Level Progression
- The game features multiple levels, each increasing in difficulty.
- As players progress, they will encounter more challenging work orders and faster enemies.
- New enemies may be introduced at certain levels to increase the challenge.

## Enemies
- **Coworkers**: Move at a moderate speed and will slow down the player upon contact.
- **Managers**: Move faster than coworkers and have a larger detection range. Contact with a manager results in a significant speed reduction for the player.

## User Interface
- The UI displays the player's current level, score, remaining time, and inventory status.
- Work orders are listed with their status (pending, in progress, completed, failed).
- A game over screen will appear when the player runs out of time or is caught too many times.

## Art and Sound
- The game will feature pixel art style graphics for characters and environments.
- Sound effects will enhance gameplay, including sounds for collecting materials, completing orders, and background music.

## Conclusion
Machinist Runner aims to provide an engaging and challenging experience for players, combining classic arcade gameplay with modern mechanics. The game encourages strategic thinking and quick reflexes as players navigate the factory, complete work orders, and avoid their coworkers and managers.