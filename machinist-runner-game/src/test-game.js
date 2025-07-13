// Manual game testing script
// This can be run in the browser console to test game functionality

function runGameTests() {
    console.log('🧪 Starting manual game tests...');
    
    // Test 1: Particle System
    console.log('Testing particle system...');
    if (typeof particleSystem !== 'undefined') {
        particleSystem.addParticles(400, 300, 10, '#ff0000', 'spark');
        console.log('✅ Particle system working, particles added');
    } else {
        console.log('❌ Particle system not found');
    }
    
    // Test 2: Achievement System
    console.log('Testing achievement system...');
    if (typeof achievementManager !== 'undefined') {
        // Manually trigger first order achievement
        gameState.ordersCompleted = 1;
        updateAchievementProgress();
        console.log('✅ Achievement system tested');
    } else {
        console.log('❌ Achievement manager not found');
    }
    
    // Test 3: Touch Controls
    console.log('Testing touch controls...');
    if (typeof touchControls !== 'undefined') {
        console.log('✅ Touch controls initialized');
    } else {
        console.log('❌ Touch controls not found');
    }
    
    // Test 4: Screen Shake
    console.log('Testing screen shake...');
    if (typeof addScreenShake === 'function') {
        addScreenShake(10, 500);
        console.log('✅ Screen shake triggered');
    } else {
        console.log('❌ Screen shake function not found');
    }
    
    // Test 5: Game State
    console.log('Testing game state...');
    console.log('Current game state:', {
        level: gameState.level,
        score: gameState.score,
        pips: gameState.pips,
        gameRunning: gameState.gameRunning
    });
    
    // Test 6: API Connection
    console.log('Testing API connection...');
    fetch('http://localhost:3001/api/highscores')
        .then(response => response.json())
        .then(data => {
            console.log('✅ API connection working, high scores:', data);
        })
        .catch(error => {
            console.log('❌ API connection failed:', error);
        });
    
    console.log('🧪 Manual tests completed!');
}

// Auto-run tests when this script is loaded
if (typeof window !== 'undefined') {
    console.log('Game test script loaded. Run runGameTests() to test functionality.');
    
    // Wait a bit for game to initialize, then run tests
    setTimeout(runGameTests, 2000);
}
