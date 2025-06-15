// filepath: /Users/sebastianszewczyk/Documents/GitHub/WebScrapper/WebScraper/public/js/script.js

document.addEventListener('DOMContentLoaded', () => {
    const provideBriefButton = document.getElementById('provideBriefButton');
    const briefContentDiv = document.getElementById('briefContent');

    provideBriefButton.addEventListener('click', async () => {
        briefContentDiv.innerHTML = '<div class="loading">Generating brief... Please wait.</div>';
        const summary = await fetchBriefSummary();
        briefContentDiv.innerHTML = summary;
    });
});

async function fetchBriefSummary() {
    try {
        const response = await fetch('/api/generate-brief');
        if (!response.ok) {
            throw new Error('Failed to generate brief');
        }
        const data = await response.json();
        return data.summary || 'No summary available.';
    } catch (error) {
        console.error('Error fetching brief summary:', error);
        return 'Error generating brief summary.';
    }
}