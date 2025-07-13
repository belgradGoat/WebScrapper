// Test script for API functionality
async function testAPI() {
    try {
        console.log('Testing high scores GET endpoint...');
        const response = await fetch('http://localhost:3001/api/highscores');
        const data = await response.json();
        console.log('✅ GET /api/highscores:', data);

        console.log('Testing high scores POST endpoint...');
        const postResponse = await fetch('http://localhost:3001/api/highscores', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name: 'Test Player',
                score: 1000,
                level: 5
            })
        });
        const postData = await postResponse.json();
        console.log('✅ POST /api/highscores:', postData);

        console.log('Testing GET again to see saved score...');
        const response2 = await fetch('http://localhost:3001/api/highscores');
        const data2 = await response2.json();
        console.log('✅ Updated high scores:', data2);

    } catch (error) {
        console.error('❌ API test failed:', error);
    }
}

testAPI();
