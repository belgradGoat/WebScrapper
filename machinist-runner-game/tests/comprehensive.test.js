// Basic unit tests for Machinist Runner game mechanics
describe('Machinist Runner Game Tests', () => {
    // Mock DOM elements for testing
    beforeEach(() => {
        global.document = {
            getElementById: jest.fn(() => ({
                textContent: '',
                innerHTML: '',
                style: {},
                appendChild: jest.fn(),
                removeChild: jest.fn()
            })),
            createElement: jest.fn(() => ({
                style: {},
                classList: { add: jest.fn(), remove: jest.fn() },
                addEventListener: jest.fn()
            })),
            addEventListener: jest.fn(),
            body: { appendChild: jest.fn() }
        };
        
        global.window = {
            addEventListener: jest.fn(),
            innerWidth: 800,
            innerHeight: 600
        };
        
        global.canvas = {
            width: 800,
            height: 600,
            getContext: jest.fn(() => ({
                clearRect: jest.fn(),
                fillRect: jest.fn(),
                arc: jest.fn(),
                fill: jest.fn(),
                stroke: jest.fn(),
                beginPath: jest.fn(),
                moveTo: jest.fn(),
                lineTo: jest.fn(),
                save: jest.fn(),
                restore: jest.fn(),
                translate: jest.fn()
            }))
        };
    });

    describe('WorkOrder Class', () => {
        test('should create work order with correct properties', () => {
            const order = new WorkOrder('Easy', 1);
            
            expect(order.difficulty).toBe('Easy');
            expect(order.level).toBe(1);
            expect(order.status).toBe('pending');
            expect(order.materialNeeded).toBe(1);
            expect(order.points).toBeGreaterThan(0);
        });

        test('should calculate correct material needed', () => {
            const easyOrder = new WorkOrder('Easy', 1);
            const mediumOrder = new WorkOrder('Medium', 1);
            const hardOrder = new WorkOrder('Hard', 1);
            
            expect(easyOrder.materialNeeded).toBe(1);
            expect(mediumOrder.materialNeeded).toBe(2);
            expect(hardOrder.materialNeeded).toBe(3);
        });

        test('should validate step progression correctly', () => {
            const order = new WorkOrder('Easy', 1);
            
            expect(order.canProgress('cad')).toBe(true);
            expect(order.canProgress('material')).toBe(true);
            expect(order.canProgress('machine')).toBe(false); // Needs CAD first
            
            order.steps.cad = true;
            global.gameState = { material: 1 };
            expect(order.canProgress('machine')).toBe(true);
        });
    });

    describe('Player Class', () => {
        test('should create player with correct initial properties', () => {
            const player = new Player(100, 100, 3);
            
            expect(player.x).toBe(100);
            expect(player.y).toBe(100);
            expect(player.speed).toBe(3);
            expect(player.baseSpeed).toBe(3);
        });

        test('should calculate distance correctly', () => {
            const player = new Player(0, 0, 3);
            const distance = player.distanceTo(3, 4);
            
            expect(distance).toBe(5); // 3-4-5 triangle
        });

        test('should handle slowdown correctly', () => {
            const player = new Player(100, 100, 3);
            player.slowDown(1000);
            
            expect(player.speed).toBe(0.9); // 30% of base speed
        });
    });

    describe('Enemy Class', () => {
        test('should create enemy with correct properties', () => {
            const enemy = new Enemy(100, 100, 'coworker');
            
            expect(enemy.x).toBe(100);
            expect(enemy.y).toBe(100);
            expect(enemy.type).toBe('coworker');
            expect(enemy.speed).toBeGreaterThan(0);
        });

        test('should have different properties for different types', () => {
            const coworker = new Enemy(0, 0, 'coworker');
            const manager = new Enemy(0, 0, 'manager');
            const hr = new Enemy(0, 0, 'hr');
            
            expect(coworker.speed).toBeLessThan(manager.speed);
            expect(hr.speed).toBeGreaterThan(coworker.speed);
        });
    });

    describe('Particle System', () => {
        test('should create particles correctly', () => {
            const particleSystem = new ParticleSystem();
            particleSystem.addParticles(100, 100, 5, '#ff0000', 'spark');
            
            expect(particleSystem.particles.length).toBe(5);
            expect(particleSystem.particles[0].color).toBe('#ff0000');
        });

        test('should update particles and remove dead ones', () => {
            const particleSystem = new ParticleSystem();
            particleSystem.addParticles(100, 100, 3, '#00ff00', 'spark');
            
            // Manually kill particles
            particleSystem.particles.forEach(p => p.life = 0);
            particleSystem.update();
            
            expect(particleSystem.particles.length).toBe(0);
        });
    });

    describe('Achievement System', () => {
        test('should create achievements correctly', () => {
            const achievement = new Achievement(
                'test_id',
                'Test Achievement',
                'Test description',
                '🏆',
                (data) => data.score >= 100,
                150
            );
            
            expect(achievement.id).toBe('test_id');
            expect(achievement.name).toBe('Test Achievement');
            expect(achievement.points).toBe(150);
            expect(achievement.unlocked).toBe(false);
        });

        test('should unlock when condition is met', () => {
            const achievement = new Achievement(
                'score_test',
                'Score Test',
                'Reach 100 points',
                '🎯',
                (data) => data.score >= 100
            );
            
            // Mock the global functions
            global.showAchievement = jest.fn();
            global.particleSystem = { addParticles: jest.fn() };
            global.player = { x: 100, y: 100 };
            global.addScreenShake = jest.fn();
            global.soundManager = { playComplete: jest.fn() };
            
            const result = achievement.check({ score: 150 });
            
            expect(result).toBe(true);
            expect(achievement.unlocked).toBe(true);
        });
    });

    describe('Game State', () => {
        test('should reset game state correctly', () => {
            global.gameState = {
                level: 5,
                score: 1000,
                pips: 2,
                gameRunning: false
            };
            
            resetGameState();
            
            expect(gameState.level).toBe(1);
            expect(gameState.score).toBe(0);
            expect(gameState.pips).toBe(0);
            expect(gameState.gameRunning).toBe(true);
        });
    });

    describe('Maze System', () => {
        test('should validate path correctly', () => {
            // Mock maze paths
            global.mazePaths = {
                paths: [{
                    start: { x: 0, y: 0 },
                    end: { x: 100, y: 0 },
                    width: 30
                }]
            };
            
            global.distance = (x1, y1, x2, y2) => 
                Math.sqrt(Math.pow(x2 - x1, 2) + Math.pow(y2 - y1, 2));
            
            // Point on the path should be valid
            expect(isOnPath(50, 0)).toBe(true);
            
            // Point off the path should be invalid
            expect(isOnPath(50, 50)).toBe(false);
        });
    });
});

// Test utilities
function createMockGameState() {
    return {
        level: 1,
        score: 0,
        pips: 0,
        material: 0,
        programs: 0,
        parts: 0,
        gameRunning: true,
        workOrders: [],
        currentOrder: null
    };
}

// Run tests if in Node.js environment
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        createMockGameState
    };
}
