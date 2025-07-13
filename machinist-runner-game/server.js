const express = require('express');
const cors = require('cors');
const fs = require('fs');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static('src'));

// High scores storage file
const scoresFile = path.join(__dirname, 'highscores.json');

// Initialize scores file if it doesn't exist
if (!fs.existsSync(scoresFile)) {
    fs.writeFileSync(scoresFile, JSON.stringify([]));
}

// Get high scores
app.get('/api/highscores', (req, res) => {
    try {
        const scores = JSON.parse(fs.readFileSync(scoresFile, 'utf8'));
        // Sort by score descending and return top 10
        const topScores = scores
            .sort((a, b) => b.score - a.score)
            .slice(0, 10);
        res.json(topScores);
    } catch (error) {
        console.error('Error reading high scores:', error);
        res.status(500).json({ error: 'Failed to read high scores' });
    }
});

// Submit new high score
app.post('/api/highscores', (req, res) => {
    try {
        const { name, score, level } = req.body;
        
        if (!name || typeof score !== 'number' || typeof level !== 'number') {
            return res.status(400).json({ error: 'Invalid data provided' });
        }
        
        const scores = JSON.parse(fs.readFileSync(scoresFile, 'utf8'));
        
        const newScore = {
            name: name.substring(0, 20), // Limit name length
            score,
            level,
            date: new Date().toISOString()
        };
        
        scores.push(newScore);
        
        // Keep only top 100 scores to prevent file from growing too large
        const sortedScores = scores
            .sort((a, b) => b.score - a.score)
            .slice(0, 100);
        
        fs.writeFileSync(scoresFile, JSON.stringify(sortedScores, null, 2));
        
        res.json({ success: true, rank: sortedScores.findIndex(s => s === newScore) + 1 });
    } catch (error) {
        console.error('Error saving high score:', error);
        res.status(500).json({ error: 'Failed to save high score' });
    }
});

// Serve the game
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'src', 'index.html'));
});

app.listen(PORT, () => {
    console.log(`Machinist Runner server running on port ${PORT}`);
    console.log(`Game available at: http://localhost:${PORT}`);
});
