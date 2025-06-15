// filepath: /Users/sebastianszewczyk/Documents/GitHub/WebScrapper/WebScraper/src/server.js
const express = require('express');
const cors = require('cors');
const fetch = require('node-fetch');

const app = express();
app.use(cors());
app.use(express.json());

const GOOGLE_GEMINI_API_KEY = 'your_google_gemini_api_key'; // Replace with your actual API key

// Main API endpoint to fetch news articles
app.get('/api/news', async (req, res) => {
    // Existing logic to fetch news articles
});

// New endpoint to generate a summary using Google Gemini API
app.post('/api/generate-brief', async (req, res) => {
    const { articles } = req.body;

    if (!articles || articles.length === 0) {
        return res.status(400).json({ error: 'No articles provided for summarization.' });
    }

    try {
        const response = await fetch('https://api.google.com/gemini/summarize', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${GOOGLE_GEMINI_API_KEY}`
            },
            body: JSON.stringify({
                documents: articles.map(article => ({
                    title: article.title,
                    content: article.description || ''
                })),
                max_length: 2000
            })
        });

        if (!response.ok) {
            throw new Error(`Error from Google Gemini API: ${response.statusText}`);
        }

        const summaryData = await response.json();
        res.json({ summary: summaryData.summary });
    } catch (error) {
        console.error('Error generating summary:', error);
        res.status(500).json({ error: 'Failed to generate summary.' });
    }
});

// Server startup
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`Server is running on http://localhost:${PORT}`);
});