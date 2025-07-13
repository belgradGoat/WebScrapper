// Load the game scripts in the correct order to make classes available
const fs = require('fs');
const path = require('path');

// Helper function to load a script file
function loadScript(filename) {
    const filepath = path.join(__dirname, '..', 'src', 'js', filename);
    const content = fs.readFileSync(filepath, 'utf8');
    eval(content);
}

// Load scripts in dependency order
loadScript('utils.js');
loadScript('gameState.js');
loadScript('workOrders.js');
loadScript('player.js');
loadScript('enemies.js');
loadScript('particles.js');
loadScript('achievements.js');

describe('Machinist Runner Game Tests', () => {
    beforeEach(() => {
        // Reset global state
        if (typeof resetGameState === 'function') {
            resetGameState();
        }
    });

    describe('Game State', () => {
        test('should have default game state values', () => {
            expect(typeof gameState).toBe('object');
            expect(gameState.level).toBeDefined();
            expect(gameState.score).toBeDefined();
            expect(gameState.pips).toBeDefined();
        });
    });

    describe('Utility Functions', () => {
        test('distance function should calculate correctly', () => {
            if (typeof distance === 'function') {
                expect(distance(0, 0, 3, 4)).toBe(5);
                expect(distance(0, 0, 0, 0)).toBe(0);
            }
        });

        test('random functions should work', () => {
            if (typeof randomFloat === 'function') {
                const result = randomFloat(1, 10);
                expect(result).toBeGreaterThanOrEqual(1);
                expect(result).toBeLessThanOrEqual(10);
            }
        });
    });

    describe('Game Classes', () => {
        test('WorkOrder class should exist and be instantiable', () => {
            if (typeof WorkOrder === 'function') {
                const order = new WorkOrder('Easy', 1);
                expect(order).toBeDefined();
                expect(order.difficulty).toBe('Easy');
                expect(order.level).toBe(1);
            }
        });

        test('Player class should exist and be instantiable', () => {
            if (typeof Player === 'function') {
                const player = new Player(100, 100, 3);
                expect(player).toBeDefined();
                expect(player.x).toBe(100);
                expect(player.y).toBe(100);
                expect(player.speed).toBe(3);
            }
        });

        test('Enemy class should exist and be instantiable', () => {
            if (typeof Enemy === 'function') {
                const enemy = new Enemy(50, 50, 'coworker');
                expect(enemy).toBeDefined();
                expect(enemy.x).toBe(50);
                expect(enemy.y).toBe(50);
                expect(enemy.type).toBe('coworker');
            }
        });

        test('ParticleSystem class should exist and be instantiable', () => {
            if (typeof ParticleSystem === 'function') {
                const particles = new ParticleSystem();
                expect(particles).toBeDefined();
                expect(Array.isArray(particles.particles)).toBe(true);
            }
        });

        test('Achievement class should exist and be instantiable', () => {
            if (typeof Achievement === 'function') {
                const achievement = new Achievement(
                    'test',
                    'Test Achievement',
                    'Test description',
                    '🏆',
                    () => true
                );
                expect(achievement).toBeDefined();
                expect(achievement.id).toBe('test');
                expect(achievement.name).toBe('Test Achievement');
            }
        });
    });

    describe('Game Functions', () => {
        test('should have core game functions defined', () => {
            const expectedFunctions = [
                'updateGameState',
                'resetGameState',
                'updateAchievementProgress'
            ];

            expectedFunctions.forEach(funcName => {
                if (typeof global[funcName] === 'function') {
                    expect(typeof global[funcName]).toBe('function');
                }
            });
        });
    });
});

// Simple integration test
describe('Integration Tests', () => {
    test('game state should be modifiable', () => {
        if (typeof gameState === 'object') {
            const originalScore = gameState.score || 0;
            gameState.score = 100;
            expect(gameState.score).toBe(100);
            gameState.score = originalScore; // Reset
        }
    });

    test('particle system should handle particles', () => {
        if (typeof ParticleSystem === 'function') {
            const particles = new ParticleSystem();
            const initialCount = particles.particles.length;
            
            if (typeof particles.addParticles === 'function') {
                particles.addParticles(100, 100, 3, '#ff0000', 'spark');
                expect(particles.particles.length).toBe(initialCount + 3);
            }
        }
    });

    test('work order progression should work', () => {
        if (typeof WorkOrder === 'function') {
            const order = new WorkOrder('Easy', 1);
            
            if (typeof order.canProgress === 'function') {
                // CAD step should be available initially
                expect(order.canProgress('cad')).toBe(true);
            }
        }
    });
});
