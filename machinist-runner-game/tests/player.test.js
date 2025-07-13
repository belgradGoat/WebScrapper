// This file contains unit tests for the Player class, verifying movement, interactions, and state management.

import { Player } from '../src/js/player.js';

describe('Player Class', () => {
    let player;

    beforeEach(() => {
        player = new Player(400, 300, 3);
    });

    test('should initialize player with correct properties', () => {
        expect(player.x).toBe(400);
        expect(player.y).toBe(300);
        expect(player.speed).toBe(3);
    });

    test('should move player correctly', () => {
        player.move('up');
        expect(player.y).toBe(297); // 300 - 3

        player.move('down');
        expect(player.y).toBe(300); // back to original position

        player.move('left');
        expect(player.x).toBe(397); // 400 - 3

        player.move('right');
        expect(player.x).toBe(400); // back to original position
    });

    test('should not move out of bounds', () => {
        player.move('left');
        player.move('left');
        player.move('left');
        player.move('left');
        player.move('left');
        expect(player.x).toBeGreaterThanOrEqual(0); // Assuming left boundary is 0

        player.move('up');
        player.move('up');
        player.move('up');
        player.move('up');
        player.move('up');
        expect(player.y).toBeGreaterThanOrEqual(0); // Assuming top boundary is 0
    });

    test('should interact with stations correctly', () => {
        const station = { action: 'cad' };
        player.interactWithStation(station);
        expect(player.programs).toBe(1); // Assuming initial programs is 0
    });

    test('should manage work orders correctly', () => {
        const order = { id: 1, status: 'pending' };
        player.selectWorkOrder(order);
        expect(player.currentOrder).toBe(order);
        expect(order.status).toBe('in_progress');
    });
});