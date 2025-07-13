// This file contains unit tests for the game logic, ensuring that the game mechanics function as expected.

import { generateWorkOrder, selectWorkOrder, updateUI } from '../src/js/game.js';
import { gameState } from '../src/js/gameState.js';

describe('Game Logic Tests', () => {
    beforeEach(() => {
        // Reset game state before each test
        gameState.level = 1;
        gameState.pips = 0;
        gameState.score = 0;
        gameState.timeLeft = 60;
        gameState.material = 0;
        gameState.programs = 0;
        gameState.parts = 0;
        gameState.currentOrder = null;
        gameState.workOrders = [];
        gameState.gameRunning = true;
    });

    test('generateWorkOrder should create a valid work order', () => {
        const order = generateWorkOrder();
        expect(order).toHaveProperty('id');
        expect(order).toHaveProperty('difficulty');
        expect(order).toHaveProperty('timeLimit');
        expect(order).toHaveProperty('materialNeeded');
        expect(order).toHaveProperty('status', 'pending');
    });

    test('selectWorkOrder should set the current order', () => {
        const order = generateWorkOrder();
        gameState.workOrders.push(order);
        selectWorkOrder(order.id);
        expect(gameState.currentOrder).toBe(order);
        expect(order.status).toBe('in_progress');
    });

    test('updateUI should update the UI elements correctly', () => {
        gameState.score = 100;
        gameState.level = 2;
        gameState.material = 5;
        updateUI();
        
        expect(document.getElementById('score').textContent).toBe('100');
        expect(document.getElementById('level').textContent).toBe('2');
        expect(document.getElementById('material').textContent).toBe('5');
    });
});