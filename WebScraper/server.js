require('dotenv').config();

// ===================================================================
// DEPENDENCIES AND SETUP
// ===================================================================
const express = require('express');
const cors = require('cors');
const fetch = require('node-fetch');
const cheerio = require('cheerio');
const puppeteer = require('puppeteer');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const { GoogleGenerativeAI } = require('@google/generative-ai');
const uri = "mongodb+srv://sszewczyk1:bvhBNFPB9eNTz5II@cluster0.lnebik8.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0";

const app = express();
app.use(cors());
app.use(express.json());

// API key for GNews service (external news API)
const GNEWS_API_KEY = 'dac11b1cf0731071bb89fbfca20fbadf';

// ===================================================================
// AI SUMMARIZATION
// ===================================================================
const GEMINI_API_KEY = process.env.GEMINI_API_KEY || "YOUR_GEMINI_API_KEY_HERE";
let genAI;
if (GEMINI_API_KEY && GEMINI_API_KEY !== "YOUR_GEMINI_API_KEY_HERE") {
    genAI = new GoogleGenerativeAI(GEMINI_API_KEY);
} else {
    console.warn('⚠️ WARNING: Gemini API key is not set or is a placeholder.');
}

app.post('/api/summarize', async (req, res) => {
    console.log('[API Call] Received request for /api/summarize');
    const { articles, prompt } = req.body;
    if (!articles || !Array.isArray(articles) || articles.length === 0) {
        return res.status(400).json({ error: 'No articles provided for summarization or articles is not an array.' });
    }
    try {
        const limitedArticles = articles.slice(0, 50);
        const cleanedArticles = limitedArticles.map(article => (typeof article === 'string'
            ? article.replace(/[\x00-\x1F\x7F-\x9F]/g, ' ').replace(/\s+/g, ' ').trim()
            : article));
        const inputData = { articles: cleanedArticles, prompt: prompt || "Create a comprehensive global situation update from these news articles." };
        const jsonString = JSON.stringify(inputData);
        let pythonCommand = 'python3';
        try {
            require('child_process').execSync('python3 --version', { stdio: 'ignore' });
        } catch (e) {
            console.log('[Python AI] python3 not found, trying python...');
            pythonCommand = 'python';
        }
        const tempFilePath = path.join(__dirname, `temp_input_${Date.now()}.json`);
        try {
            fs.writeFileSync(tempFilePath, jsonString, 'utf8');
            const scriptName = 'simple_news_summarizer.py';
            const pythonProcess = spawn(pythonCommand, [scriptName, tempFilePath], {
                cwd: __dirname,
                stdio: ['pipe', 'pipe', 'pipe'],
                timeout: 60000
            });
            let outputData = '';
            let errorData = '';
            let processFinished = false;
            const timeoutHandler = setTimeout(() => {
                if (!processFinished) {
                    console.error('❌ Python process timed out');
                    pythonProcess.kill('SIGKILL');
                    if (!res.headersSent) res.status(500).json({ error: 'Python summarizer timed out' });
                }
            }, 60000);
            pythonProcess.stdout.on('data', (data) => { outputData += data.toString(); });
            pythonProcess.stderr.on('data', (data) => { errorData += data.toString(); });
            pythonProcess.on('close', (code) => {
                clearTimeout(timeoutHandler);
                processFinished = true;
                try { fs.unlinkSync(tempFilePath); } catch (cleanupError) { console.error(`[AI] Warning: ${cleanupError.message}`); }
                if (res.headersSent) return;
                if (code === 0) {
                    try {
                        const cleanOutput = outputData.trim();
                        if (!cleanOutput) {
                            return res.status(500).json({ error: 'Python script produced no output.' });
                        }
                        const result = JSON.parse(cleanOutput);
                        if (result.error) {
                            res.status(500).json({ error: result.error });
                        } else if (result.summary) {
                            res.json(result);
                        } else {
                            res.status(500).json({ error: 'Unexpected summarizer output.' });
                        }
                    } catch (parseError) {
                        res.status(500).json({ error: `Failed to parse summarizer output: ${parseError.message}` });
                    }
                } else {
                    res.status(500).json({ error: `Python summarizer process failed (exit code: ${code}). Error: ${errorData}` });
                }
            });
            pythonProcess.on('error', (error) => {
                clearTimeout(timeoutHandler);
                processFinished = true;
                try { fs.unlinkSync(tempFilePath); } catch (cleanupError) { console.error(`[Python AI] ${cleanupError.message}`); }
                res.status(500).json({ error: `Failed to start Python process: ${error.message}` });
            });
        } catch (fileError) {
            res.status(500).json({ error: `Failed to prepare input data: ${fileError.message}` });
        }
    } catch (error) {
        if (!res.headersSent) res.status(500).json({ error: `Server error: ${error.message}` });
    }
});
// ===================================================================
// GEMMA + MONGODB SUMMARIZATION
// ===================================================================
app.post('/api/summarize-gemma', async (req, res) => {
    console.log('[API Call] Received request for /api/summarize-gemma');
    const { articles, prompt } = req.body;
    
    if (!articles || !Array.isArray(articles) || articles.length === 0) {
        return res.status(400).json({ error: 'No articles provided for summarization.' });
    }
    
    try {
        const limitedArticles = articles.slice(0, 100);
        const cleanedArticles = limitedArticles.map(article => {
            if (typeof article === 'string') {
                return { description: article.replace(/[\x00-\x1F\x7F-\x9F]/g, ' ').replace(/\s+/g, ' ').trim() };
            }
            return {
                ...article,
                title: article.title?.replace(/[\x00-\x1F\x7F-\x9F]/g, ' ').replace(/\s+/g, ' ').trim(),
                description: article.description?.replace(/[\x00-\x1F\x7F-\x9F]/g, ' ').replace(/\s+/g, ' ').trim()
            };
        });
        
        const inputData = { 
            articles: cleanedArticles, 
            prompt: prompt || "Create a comprehensive global situation update from these news articles."
        };
        
        const jsonString = JSON.stringify(inputData);
        
        let pythonCommand = 'python3';
        try {
            require('child_process').execSync('python3 --version', { stdio: 'ignore' });
        } catch (e) {
            console.log('[Gemma AI] python3 not found, trying python...');
            pythonCommand = 'python';
        }
        
        const tempFilePath = path.join(__dirname, `temp_gemma_input_${Date.now()}.json`);
        
        try {
            fs.writeFileSync(tempFilePath, jsonString, 'utf8');
            
            // Use the updated simple_gemma_summarizer.py
            const pythonProcess = spawn(pythonCommand, ['simple_gemma_summarizer.py', tempFilePath], {
                cwd: __dirname,
                stdio: ['pipe', 'pipe', 'pipe'],
                timeout: 90000
            });
            
            let outputData = '';
            let errorData = '';
            let processFinished = false;
            
            const timeoutHandler = setTimeout(() => {
                if (!processFinished) {
                    console.error('❌ Gemma process timed out');
                    pythonProcess.kill('SIGKILL');
                    if (!res.headersSent) {
                        res.status(500).json({ error: 'Gemma summarizer timed out' });
                    }
                }
            }, 90000);
            
            pythonProcess.stdout.on('data', (data) => {
                outputData += data.toString();
            });
            
            pythonProcess.stderr.on('data', (data) => {
                errorData += data.toString();
            });
            
            pythonProcess.on('close', (code) => {
                clearTimeout(timeoutHandler);
                processFinished = true;
                
                try {
                    fs.unlinkSync(tempFilePath);
                } catch (cleanupError) {
                    console.error(`[Gemma AI] Cleanup warning: ${cleanupError.message}`);
                }
                
                if (res.headersSent) return;
                
                if (code === 0) {
                    try {
                        const cleanOutput = outputData.trim();
                        if (!cleanOutput) {
                            return res.status(500).json({ error: 'Gemma script produced no output.' });
                        }
                        
                        const result = JSON.parse(cleanOutput);
                        
                        if (result.error) {
                            res.status(500).json({ error: result.error });
                        } else if (result.summary) {
                            res.json(result);
                        } else {
                            res.status(500).json({ error: 'Unexpected Gemma output.' });
                        }
                    } catch (parseError) {
                        console.error('Parse error:', parseError.message);
                        res.status(500).json({ error: `Failed to parse Gemma output: ${parseError.message}` });
                    }
                } else {
                    console.error(`Gemma process failed (code: ${code}). Error: ${errorData}`);
                    res.status(500).json({ error: `Gemma summarizer failed: ${errorData}` });
                }
            });
            
            pythonProcess.on('error', (error) => {
                clearTimeout(timeoutHandler);
                processFinished = true;
                try { fs.unlinkSync(tempFilePath); } catch {}
                if (!res.headersSent) {
                    res.status(500).json({ error: `Failed to start Gemma process: ${error.message}` });
                }
            });
            
        } catch (fileError) {
            res.status(500).json({ error: `Failed to prepare input data: ${fileError.message}` });
        }
        
    } catch (error) {
        console.error('Gemma API error:', error);
        if (!res.headersSent) {
            res.status(500).json({ error: `Server error: ${error.message}` });
        }
    }
});

// ===================================================================
// MONGODB SUMMARY RETRIEVAL
// ===================================================================
app.get('/api/summaries', async (req, res) => {
    console.log('[API Call] Received request for /api/summaries');
    
    try {
        let pythonCommand = 'python3';
        try {
            require('child_process').execSync('python3 --version', { stdio: 'ignore' });
        } catch (e) {
            pythonCommand = 'python';
        }
        
        const pythonProcess = spawn(pythonCommand, ['-c', `
import json
from pymongo import MongoClient
import os

try:
    # Use MongoDB Atlas connection
    mongo_uri = "mongodb+srv://sszewczyk1:bvhBNFPB9eNTz5II@cluster0.lnebik8.mongodb.net/eagle_watchtower?retryWrites=true&w=majority&appName=Cluster0"
    client = MongoClient(mongo_uri)
    
    # Test connection
    client.admin.command('ping')
    
    db = client['eagle_watchtower']
    summaries = list(db['summaries'].find().sort("timestamp", -1).limit(10))
    
    for summary in summaries:
        summary['_id'] = str(summary['_id'])
        summary['timestamp'] = summary['timestamp'].isoformat()
    
    print(json.dumps({"success": True, "summaries": summaries, "source": "MongoDB Atlas"}))
    
except Exception as e:
    # Fallback to local file
    try:
        import json
        if os.path.exists('summaries_history.json'):
            with open('summaries_history.json', 'r', encoding='utf-8') as f:
                summaries = json.load(f)
            print(json.dumps({"success": True, "summaries": summaries[:10], "source": "Local File"}))
        else:
            print(json.dumps({"success": True, "summaries": [], "source": "No Data"}))
    except:
        print(json.dumps({"success": False, "error": str(e)}))
`], {
            stdio: ['pipe', 'pipe', 'pipe'],
            timeout: 10000
        });
        
        let outputData = '';
        let errorData = '';
        
        pythonProcess.stdout.on('data', (data) => {
            outputData += data.toString();
        });
        
        pythonProcess.stderr.on('data', (data) => {
            errorData += data.toString();
        });
        
        pythonProcess.on('close', (code) => {
            if (code === 0) {
                try {
                    const result = JSON.parse(outputData.trim());
                    res.json(result);
                } catch (parseError) {
                    res.status(500).json({ error: 'Failed to parse MongoDB response' });
                }
            } else {
                res.status(500).json({ error: `MongoDB query failed: ${errorData}` });
            }
        });
        
    } catch (error) {
        res.status(500).json({ error: `Server error: ${error.message}` });
    }
});

// ===================================================================
// SITE-SPECIFIC SCRAPER CONFIGURATION & NEWS SOURCES
// ===================================================================
const SCRAPER_CONFIG = {
    'techcrunch.com': {
        isDynamic: false,
        selectors: {
            container: 'div.post-block, article.post-block',
            title: 'a.post-block__title__link, h2.post-block__title a',
            link: 'a.post-block__title__link, h2.post-block__title a',
            excerpt: 'div.post-block__content, .post-block__excerpt'
        }
    },
    'aljazeera.com': {
        isDynamic: true,
        selectors: {
            container: 'article.gc.u-clickable-card, .search-result',
            title: 'h3.gc__title span, h3 a',
            link: 'a.u-clickable-card__link, h3 a',
            excerpt: 'div.gc__excerpt p, .summary'
        }
    },
    'arstechnica.com': {
        isDynamic: false,
        selectors: {
            container: 'li.article, article',
            title: 'header h2 a, h2 a, h1 a',
            link: 'header h2 a, h2 a, h1 a',
            excerpt: 'p.excerpt, .summary'
        }
    },
    'news.ycombinator.com': {
        isDynamic: false,
        selectors: {
            container: '.athing',
            title: '.titleline > a',
            link: '.titleline > a',
            excerpt: ''
        }
    },
    'politico.com': {
        isDynamic: false,
        selectors: {
            container: 'li.story-frag, article',
            title: 'h3 a, h2 a',
            link: 'h3 a, h2 a',
            excerpt: 'p.summary, .summary'
        }
    },
    'reuters.com': {
        isDynamic: true,
        selectors: {
            container: '[data-testid="MediaStoryCard"], article',
            title: '[data-testid="Heading"], h3 a',
            link: 'a',
            excerpt: '[data-testid="Body"], .summary'
        }
    },
    'apnews.com': {
        isDynamic: true,
        selectors: {
            container: 'div.Card, .SearchResultsModule-results div',
            title: 'h3, .CardHeadline',
            link: 'a.Link, a',
            excerpt: 'div.CardContent, .summary'
        }
    },
    'bloomberg.com': {
        isDynamic: true,
        selectors: {
            container: 'article, .story-package-module__story',
            title: 'h3 a, .headline',
            link: 'a',
            excerpt: '.summary, .abstract'
        }
    },
    'bbc.com': {
        isDynamic: false,
        selectors: {
            container: '[data-testid="card"], .media__content',
            title: '[data-testid="card-headline"], h3 a',
            link: 'a',
            excerpt: '[data-testid="card-description"], .media__summary'
        }
    },
    'dw.com': {
        isDynamic: false,
        selectors: {
            container: '.searchResult, article',
            title: '.searchResult h2 a, h2 a',
            link: '.searchResult h2 a, h2 a',
            excerpt: '.searchResult .intro, .summary'
        }
    }
};

const NEWS_SOURCES = {
    technology: [
        { url: 'https://techcrunch.com/search/{keyword}/', scraperKey: 'techcrunch.com' },
        { url: 'https://www.aljazeera.com/search/{keyword}', scraperKey: 'aljazeera.com' },
        { url: 'https://arstechnica.com/search/?query={keyword}', scraperKey: 'arstechnica.com' },
        { url: 'https://news.ycombinator.com/search?q={keyword}', scraperKey: 'news.ycombinator.com' }
    ],
    ForeignMinisters: [
        { url: 'https://techcrunch.com/search/{keyword}/', scraperKey: 'techcrunch.com' },
        { url: 'https://www.aljazeera.com/search/{keyword}', scraperKey: 'aljazeera.com' },
        { url: 'https://arstechnica.com/search/?query={keyword}', scraperKey: 'arstechnica.com' },
        { url: 'https://news.ycombinator.com/search?q={keyword}', scraperKey: 'news.ycombinator.com' }
    ],
    politics: [
        { url: 'https://www.politico.com/search?q={keyword}', scraperKey: 'politico.com' },
        { url: 'https://www.reuters.com/search/news?blob={keyword}', scraperKey: 'reuters.com' },
        { url: 'https://apnews.com/search?q={keyword}', scraperKey: 'apnews.com' }
    ],
    business: [
        { url: 'https://www.bloomberg.com/search?query={keyword}', scraperKey: 'bloomberg.com' }
    ],
    world: [
        { url: 'https://www.bbc.com/search?q={keyword}', scraperKey: 'bbc.com' },
        { url: 'https://www.aljazeera.com/search/{keyword}', scraperKey: 'aljazeera.com' },
        { url: 'https://www.dw.com/search/?languageCode=en&item={keyword}', scraperKey: 'dw.com' }
    ]
};

const GENERIC_SOURCES = [
    { url: 'https://www.bbc.com/search?q={keyword}', scraperKey: 'bbc.com' },
    { url: 'https://www.aljazeera.com/search/{keyword}', scraperKey: 'aljazeera.com' }
];

// ===================================================================
// MAIN API ENDPOINT
// ===================================================================
app.get('/api/news', async (req, res) => {
    try {
        const { q, lang, country, max } = req.query;
        const keyword = q || 'technology';
        const maxResults = parseInt(max) || 10;
        const articlesToFetchPerSource = Math.max(maxResults * 2, 20);
        console.log(`\n🔍 Searching for "${keyword}" (target: ${maxResults} articles)`);
        
        let allArticles = [];
        
        // Source 1: GNews API
        console.log(`[API_CALL] Attempting GNews API for "${keyword}"...`);
        try {
            const gnewsData = await fetchFromGNews(keyword, lang, country, articlesToFetchPerSource);
            if (gnewsData && gnewsData.articles && gnewsData.articles.length > 0) {
                const gnewsArticles = gnewsData.articles.map(article => ({
                    ...article,
                    source: { ...article.source, type: 'GNews API' }
                }));
                allArticles.push(...gnewsArticles);
                console.log(`  ✅ GNews API: Fetched ${gnewsData.articles.length} articles.`);
            }
        } catch (gnewsError) {
            console.log(`  ❌ GNews API error:`, gnewsError.message);
        }
        
        // Source 2: Web Scraping
        console.log(`[API_CALL] Attempting Web Scraping for "${keyword}"...`);
        try {
            const scrapedArticles = await scrapeNewsFromSources(keyword, articlesToFetchPerSource);
            if (scrapedArticles.length > 0) {
                allArticles.push(...scrapedArticles);
                console.log(`  ✅ Web Scraping: Fetched ${scrapedArticles.length} articles.`);
            }
        } catch (scrapeError) { console.log(`  ❌ Web Scraping error:`, scrapeError.message); }
        
        // Source 3: Google News RSS
        console.log(`[API_CALL] Attempting Google News RSS for "${keyword}"...`);
        try {
            const googleNewsArticles = await scrapeGoogleNews(keyword, articlesToFetchPerSource);
            if (googleNewsArticles.length > 0) {
                allArticles.push(...googleNewsArticles);
                console.log(`  ✅ Google News RSS: Fetched ${googleNewsArticles.length} articles.`);
            }
        } catch (googleError) { console.log(`  ❌ Google News RSS error:`, googleError.message); }
        
        // Source 4: Guardian API
        console.log(`[API_CALL] Attempting Guardian API for "${keyword}"...`);
        try {
            const guardianArticles = await fetchFromGuardianAPI(keyword, articlesToFetchPerSource);
            if (guardianArticles.length > 0) {
                allArticles.push(...guardianArticles);
                console.log(`  ✅ Guardian API: Fetched ${guardianArticles.length} articles.`);
            }
        } catch (guardianError) { console.log(`  ❌ Guardian API error:`, guardianError.message); }
        
        console.log(`[PROCESSING] Total articles collected: ${allArticles.length}`);
        const uniqueArticles = removeDuplicates(allArticles);
        const sortedArticles = uniqueArticles
            .filter(article => article.publishedAt)
            .sort((a, b) => new Date(b.publishedAt) - new Date(a.publishedAt))
            .slice(0, maxResults);
        
        if (sortedArticles.length > 0) {
            const sourceTypes = [...new Set(sortedArticles.map(a => a.source.type))];
            console.log(`📰 Returning ${sortedArticles.length} articles.`);
            return res.json({
                totalArticles: sortedArticles.length,
                articles: sortedArticles,
                sources: sourceTypes,
                searchTerm: keyword,
                timestamp: new Date().toISOString()
            });
        } else {
            console.log(`📝 No articles found for "${keyword}". Returning mock data.`);
            return res.json(generateRecentMockNews(keyword, maxResults));
        }
        
    } catch (error) {
        console.error(`❌ Major error in /api/news:`, error);
        const maxResults = parseInt(req.query.max) || 10;
        res.status(500).json({ 
            error: error.message,
            articles: generateRecentMockNews(req.query.q || 'news', maxResults).articles
        });
    }
});

// ===================================================================
// ALL SCRAPING FUNCTIONS
// ===================================================================
async function scrapeNewsFromSources(keyword, maxNeeded) {
    console.log(`  [Scraper] Initiated for keyword: "${keyword}"`);
    let browser = null;
    
    try {
        const collectedArticles = [];
        const category = detectCategory(keyword);
        console.log(`    [Scraper] Detected category: "${category}" for keyword "${keyword}"`);
        
        let sourcesToAttempt = NEWS_SOURCES[category];
        let sourceOrigin = `NEWS_SOURCES["${category}"]`;

        if (!sourcesToAttempt || sourcesToAttempt.length === 0) {
            sourcesToAttempt = GENERIC_SOURCES;
            sourceOrigin = 'GENERIC_SOURCES (fallback)';
        }
        
        console.log(`    [Scraper] Using ${sourceOrigin}. Will attempt ALL sites from this list.`);

        browser = await puppeteer.launch({ 
            headless: 'new',
            args: ['--no-sandbox', '--disable-setuid-sandbox']
        });

        for (const source of sourcesToAttempt) {
            const config = SCRAPER_CONFIG[source.scraperKey];
            if (!config) {
                console.log(`      [Scraper] ⚠️ No config found for ${source.scraperKey}, skipping.`);
                continue;
            }

            const url = source.url.replace('{keyword}', encodeURIComponent(keyword));
            let siteArticles = [];

            try {
                if (config.isDynamic) {
                    console.log(`      [Scraper] -> Using Puppeteer for ${source.scraperKey}`);
                    siteArticles = await scrapeWithPuppeteerNew(browser, url, config.selectors, source.scraperKey);
                } else {
                    console.log(`      [Scraper] -> Using Cheerio for ${source.scraperKey}`);
                    siteArticles = await scrapeWithCheerio(url, config.selectors, source.scraperKey);
                }

                const validArticles = siteArticles.filter(article => {
                    if (!article.url || !article.title) return false;
                    
                    if (article.url.includes('/tag/') || 
                        article.url.includes('/category/') ||
                        article.title.toLowerCase().includes('today\'s latest from al jazeera') ||
                        article.title.toLowerCase().includes('| today\'s latest from')) {
                        console.log(`        [Filter] Excluding tag/category page: ${article.title} (${article.url})`);
                        return false;
                    }
                    
                    return true;
                });

                if (validArticles.length > 0) {
                    const articlesWithSource = validArticles.map(article => ({
                        ...article,
                        source: {
                            name: getDomain(url),
                            url: getDomain(url),
                            type: `Web Scrape (${config.isDynamic ? 'Puppeteer' : 'Cheerio'})`
                        }
                    }));
                    collectedArticles.push(...articlesWithSource);
                    console.log(`        [Scraper] <- Fetched ${validArticles.length} valid articles from ${source.scraperKey}`);
                } else {
                    console.log(`        [Scraper] <- No valid articles found on ${source.scraperKey}`);
                }
            } catch (error) {
                console.error(`        [Scraper] XXX Error processing ${source.scraperKey}: ${error.message}`);
            }
        }
        
        console.log(`  [Scraper] Finished. Total collected for "${keyword}": ${collectedArticles.length}`);
        return collectedArticles;
        
    } finally {
        if (browser) {
            await browser.close();
            console.log(`    [Scraper] Browser closed.`);
        }
    }
}

async function scrapeWithCheerio(url, selectors, siteName) {
    console.log(`        [Cheerio] Scraping ${siteName}: ${url.substring(0, 80)}...`);
    
    const response = await fetch(url, {
        headers: { 
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36' 
        },
        timeout: 15000
    });
    
    if (!response.ok) {
        throw new Error(`HTTP error ${response.status}`);
    }
    
    const html = await response.text();
    const $ = cheerio.load(html);
    const articles = [];

    const containerSelectors = selectors.container.split(',').map(s => s.trim());
    
    for (const containerSelector of containerSelectors) {
        const containers = $(containerSelector);
        console.log(`          [Cheerio] Trying container selector "${containerSelector}": found ${containers.length} containers`);
        
        if (containers.length > 0) {
            containers.each((i, element) => {
                if (articles.length >= 5) return false;
                
                const $container = $(element);
                
                const titleSelectors = selectors.title.split(',').map(s => s.trim());
                let title = '';
                let linkUrl = '';
                
                for (const titleSelector of titleSelectors) {
                    const titleElement = $container.find(titleSelector).first();
                    if (titleElement.length > 0) {
                        title = titleElement.text().trim();
                        linkUrl = titleElement.attr('href') || $container.find(selectors.link.split(',')[0].trim()).first().attr('href');
                        break;
                    }
                }
                
                if (!title || !linkUrl) return true;
                
                let fullUrl;
                try {
                    fullUrl = linkUrl.startsWith('http') ? linkUrl : new URL(linkUrl, new URL(url).origin).href;
                } catch (urlError) {
                    console.log(`            [Cheerio] Invalid URL "${linkUrl}" from ${siteName}`);
                    return true;
                }

                if (fullUrl.includes('/tag/') || 
                    fullUrl.includes('/category/') ||
                    title.toLowerCase().includes('today\'s latest from al jazeera') ||
                    title.toLowerCase().includes('| today\'s latest from')) {
                    console.log(`        [Filter] Excluding tag/category page: ${title} (${fullUrl})`);
                    return true;
                }
                
                let excerpt = '';
                if (selectors.excerpt) {
                    const excerptSelectors = selectors.excerpt.split(',').map(s => s.trim());
                    for (const excerptSelector of excerptSelectors) {
                        const excerptElement = $container.find(excerptSelector).first();
                        if (excerptElement.length > 0) {
                            excerpt = excerptElement.text().trim();
                            break;
                        }
                    }
                }
                
                let publishedAt = extractPublishedDate($container, siteName, fullUrl);
                
                if (title.length > 10 && !title.toLowerCase().includes("more news")) {
                    articles.push({
                        title: title,
                        url: fullUrl,
                        description: excerpt || `Article about the search topic from ${siteName}`,
                        publishedAt: publishedAt
                    });
                }
            });
            
            if (articles.length > 0) break;
        }
    }
    
    console.log(`          [Cheerio] Finished ${siteName}. Found ${articles.length} articles.`);
    return articles;
}

async function scrapeWithPuppeteerNew(browser, url, selectors, siteName) {
    console.log(`        [Puppeteer] Scraping ${siteName}: ${url.substring(0, 80)}...`);
    
    const page = await browser.newPage();
    await page.setUserAgent('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36');

    try {
        await page.goto(url, { waitUntil: 'networkidle2', timeout: 30000 });
        
        const containerSelectors = selectors.container.split(',').map(s => s.trim());
        let selectorFound = false;
        
        for (const containerSelector of containerSelectors) {
            try {
                await page.waitForSelector(containerSelector, { timeout: 5000 });
                selectorFound = true;
                console.log(`          [Puppeteer] Found container selector: ${containerSelector}`);
                break;
            } catch (e) {
                // Selector not found, try next
            }
        }
        
        if (!selectorFound) {
            console.log(`          [Puppeteer] No article container selectors found for ${siteName}`);
            await page.close();
            return [];
        }
        
        const articles = await page.evaluate((s, site, pageUrl) => {
            const results = [];
            const containerSelectorsEval = s.container.split(',').map(cs => cs.trim());
            
            for (const containerSelector of containerSelectorsEval) {
                const containers = document.querySelectorAll(containerSelector);
                if (containers.length > 0) {
                    containers.forEach((container) => {
                        if (results.length >= 5) return;

                        const titleSelectorsEval = s.title.split(',').map(ts => ts.trim());
                        let title = '';
                        let link = '';
                        for (const titleSelector of titleSelectorsEval) {
                            const titleElement = container.querySelector(titleSelector);
                            if (titleElement) {
                                title = titleElement.innerText?.trim() || titleElement.textContent?.trim();
                                link = titleElement.href || container.querySelector(s.link.split(',')[0].trim())?.href;
                                break;
                            }
                        }

                        if (!title || !link) return;

                        if (link.includes('/tag/') || 
                            link.includes('/category/') ||
                            title.toLowerCase().includes('today\'s latest from al jazeera') ||
                            title.toLowerCase().includes('| today\'s latest from')) {
                            return;
                        }

                        let excerpt = '';
                        if (s.excerpt) {
                            const excerptSelectorsEval = s.excerpt.split(',').map(es => es.trim());
                            for (const excerptSelector of excerptSelectorsEval) {
                                const excerptElement = container.querySelector(excerptSelector);
                                if (excerptElement) {
                                    excerpt = excerptElement.innerText?.trim() || excerptElement.textContent?.trim();
                                    break;
                                }
                            }
                        }
                        
                        const publishedAt = new Date().toISOString();
                        
                        if (title.length > 10 && !title.toLowerCase().includes("more news")) {
                            results.push({
                                title: title,
                                url: link,
                                description: excerpt || `Article about the search topic from ${site}`,
                                publishedAt: publishedAt
                            });
                        }
                    });
                    if (results.length > 0) break; 
                }
            }
            return results;
        }, selectors, siteName, url);

        console.log(`          [Puppeteer] Finished ${siteName}. Found ${articles.length} articles.`);
        await page.close();
        return articles;
        
    } catch (error) {
        console.error(`          [Puppeteer] Error scraping ${siteName}: ${error.message}`);
        if (page && !page.isClosed()) {
            await page.close();
        }
        return [];
    }
}

async function fetchFromGNews(keyword, lang, country, max) {
    const params = new URLSearchParams({
        q: keyword,
        lang: lang || 'en',
        country: country || 'us',
        max: max || '10',
        apikey: GNEWS_API_KEY
    });
    
    const response = await fetch(`https://gnews.io/api/v4/search?${params.toString()}`);
    
    if (!response.ok) {
        throw new Error(`GNews API error: ${response.status}`);
    }
    
    return await response.json();
}

async function scrapeGoogleNews(keyword, maxResults) {
    try {
        const url = `https://news.google.com/rss/search?q=${encodeURIComponent(keyword)}&hl=en&gl=US&ceid=US:en`;
        
        const response = await fetch(url, {
            headers: {
                'User-Agent': 'Mozilla/5.0 (compatible; NewsBot/1.0)'
            }
        });
        
        const xmlText = await response.text();
        const $ = cheerio.load(xmlText, { xmlMode: true });
        const articles = [];
        
        $('item').each((i, element) => {
            if (i >= maxResults) return false;
            
            const $item = $(element);
            const title = $item.find('title').text();
            const link = $item.find('link').text();
            const description = $item.find('description').text().replace(/<[^>]*>/g, '');
            const pubDate = $item.find('pubDate').text();
            
            if (title && link) {
                articles.push({
                    title: title,
                    description: description || `Google News article about ${keyword}`,
                    url: link,
                    urlToImage: null,
                    publishedAt: pubDate ? new Date(pubDate).toISOString() : new Date().toISOString(),
                    source: {
                        name: 'Google News',
                        url: 'news.google.com',
                        type: 'Google News RSS'
                    }
                });
            }
        });
        
        return articles;
        
    } catch (error) {
        console.log('Google News scraping error:', error.message);
        return [];
    }
}

async function fetchFromGuardianAPI(keyword, maxResults) {
    try {
        const GUARDIAN_API_KEY = 'f66ca23b-5fd8-4869-9aff-6256719af4ce';
        
        if (!GUARDIAN_API_KEY) {
            console.log('⚠️ Guardian API key not configured, skipping Guardian source');
            return [];
        }
        
        const url = `https://content.guardianapis.com/search?q=${encodeURIComponent(keyword)}&page-size=${Math.min(maxResults, 50)}&show-fields=headline,byline,thumbnail,short-url,body&show-tags=keyword&api-key=${GUARDIAN_API_KEY}`;
        
        console.log(`[Guardian API] Searching for: "${keyword}"`);
        
        const response = await fetch(url, {
            headers: {
                'User-Agent': 'NewsAggregator/1.0'
            },
            timeout: 15000
        });
        
        if (!response.ok) {
            throw new Error(`Guardian API error: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (!data.response || !data.response.results) {
            throw new Error('Invalid response format from Guardian API');
        }
        
        const articles = data.response.results.map(item => {
            return {
                title: item.fields?.headline || item.webTitle,
                description: item.fields?.body ? 
                    item.fields.body.replace(/<[^>]*>/g, '').substring(0, 200) + '...' : 
                    `Guardian article about ${keyword}`,
                url: item.fields?.shortUrl || item.webUrl,
                urlToImage: item.fields?.thumbnail || null,
                publishedAt: item.webPublicationDate,
                source: {
                    name: 'The Guardian',
                    url: 'theguardian.com',
                    type: 'Guardian API'
                }
            };
        });
        
        console.log(`[Guardian API] Fetched ${articles.length} articles`);
        return articles;
        
    } catch (error) {
        console.log('[Guardian API] Error:', error.message);
        return [];
    }
}

// Extracts the published date from the article container using various selectors or patterns
// If no date is found, it falls back to the current date
// Supports both selector-based extraction and pattern-based extraction from text content
// Returns the date in ISO format

function extractPublishedDate($container, siteName, articleUrl) {
    // Try existing selector-based extraction first
    const now = new Date();
    const dateSelectors = {
        'aljazeera.com': [
            { selector: 'time[datetime]', attribute: 'datetime' },
            { selector: '.gc__date time', attribute: 'datetime' },
            { selector: '.gc__date', text: true }
        ],
        // ... other site selectors ...
    };
    
    const siteSpecificSelectors = dateSelectors[siteName] || [];
    const genericSelectors = [
        { selector: 'time[datetime]', attribute: 'datetime' },
        { selector: '.date', text: true },
        { selector: 'time', text: true }
    ];

    const allSelectorsToTry = [...siteSpecificSelectors, ...genericSelectors];

    // First try to extract using DOM selectors
    for (const selObj of allSelectorsToTry) {
        const dateElement = $container.find(selObj.selector).first();
        if (dateElement.length > 0) {
            let dateStr = selObj.attribute ? dateElement.attr(selObj.attribute) : dateElement.text().trim();
            
            if (dateStr) {
                let cleanedDateStr = dateStr.replace(/(Published\s*(on)?|Updated|Last update on|ET|\s*\|.*)/gi, '').trim();
                const parsed = new Date(cleanedDateStr);
                if (!isNaN(parsed.getTime()) && parsed < now && parsed > new Date('2010-01-01')) {
                    return parsed.toISOString();
                }
            }
        }
    }
    
    // If selector-based extraction failed, try pattern-based extraction from text content
    if (siteName === 'aljazeera.com' || articleUrl.includes('aljazeera.com')) {
        const articleText = $container.text();
        return extractDateFromText(articleText, now) || now.toISOString();
    }
    
    return now.toISOString();
}

// Add this new helper function for pattern-based date extraction
function extractDateFromText(text, currentDate = new Date()) {
    // Common date patterns found in news articles
    const datePatterns = [
        // "December 15, 2023", "Dec 15, 2023", "15 December 2023"
        /(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{4})/i,
        /(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2}),?\s+(\d{4})/i,
        
        // "2023-12-15", "2023/12/15"
        /(\d{4})[-\/](\d{1,2})[-\/](\d{1,2})/,
        
        // "15/12/2023", "15-12-2023" (European format)
        /(\d{1,2})[-\/](\d{1,2})[-\/](\d{4})/,
        
        // ISO format "2023-12-15T10:30:00Z"
        /(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})/,
        
        // "Published: December 15, 2023", "Updated: Dec 15, 2023"
        /(?:Published|Updated|Posted):\s*(\w+\s+\d{1,2},?\s+\d{4})/i,
        
        // "15 hours ago", "2 days ago", etc.
        /(\d+)\s+(hours?|days?|weeks?|months?)\s+ago/i
    ];
    
    for (const pattern of datePatterns) {
        const match = text.match(pattern);
        if (match) {
            try {
                let extractedDate;
                
                // Handle relative dates like "2 days ago"
                if (match[0].includes('ago')) {
                    const amount = parseInt(match[1]);
                    const unit = match[2].toLowerCase();
                    extractedDate = new Date(currentDate);
                    
                    if (unit.includes('hour')) {
                        extractedDate.setHours(extractedDate.getHours() - amount);
                    } else if (unit.includes('day')) {
                        extractedDate.setDate(extractedDate.getDate() - amount);
                    } else if (unit.includes('week')) {
                        extractedDate.setDate(extractedDate.getDate() - (amount * 7));
                    } else if (unit.includes('month')) {
                        extractedDate.setMonth(extractedDate.getMonth() - amount);
                    }
                } else {
                    // Parse the extracted date string
                    extractedDate = new Date(match[0].replace(/(?:Published|Updated|Posted):\s*/i, ''));
                }
                
                // Validate the date
                if (!isNaN(extractedDate.getTime()) && extractedDate <= currentDate) {
                    return extractedDate.toISOString();
                }
            } catch (e) {
                console.warn('Failed to parse date:', match[0], e);
            }
        }
    }
    
    return null;
}
// ===================================================================
// BLUESKY API INTEGRATION
// ===================================================================
app.post('/api/bluesky', async (req, res) => {
    console.log('[API Call] Received request for /api/bluesky');
    const { query, limit } = req.body;

    if (!query || typeof query !== 'string' || query.trim().length === 0) {
        return res.status(400).json({ error: 'Search query is required and must be a non-empty string.' });
    }

    try {
        const searchLimit = Math.min(limit || 100, 100);
        console.log(`[Bluesky] Searching for: "${query}" (limit: ${searchLimit})`);
        
        let pythonCommand = 'python3';
        
        try {
            require('child_process').execSync('python3 --version', { stdio: 'ignore' });
        } catch (e) {
            console.log('[Bluesky] python3 not found, trying python...');
            pythonCommand = 'python';
        }
        
        console.log(`[Bluesky] Using command: ${pythonCommand}`);
        
        const pythonProcess = spawn(pythonCommand, ['bluesky_scraper.py', query, searchLimit.toString()], {
            cwd: __dirname,
            stdio: ['pipe', 'pipe', 'pipe'],
            timeout: 30000
        });
        
        let outputData = '';
        let errorData = '';
        let processFinished = false;
        
        const timeoutHandler = setTimeout(() => {
            if (!processFinished) {
                console.error('❌ Bluesky Python process timed out');
                pythonProcess.kill('SIGKILL');
                if (!res.headersSent) {
                    res.status(500).json({ error: 'Bluesky search timed out' });
                }
            }
        }, 30000);
        
        pythonProcess.stdout.on('data', (data) => {
            outputData += data.toString();
        });
        
        pythonProcess.stderr.on('data', (data) => {
            const errorText = data.toString();
            errorData += errorText;
            console.log(`[Bluesky stderr]: ${errorText}`);
        });
        
        pythonProcess.on('close', (code) => {
            clearTimeout(timeoutHandler);
            processFinished = true;
            
            console.log(`[Bluesky] Process exited with code: ${code}`);
            
            if (res.headersSent) {
                console.log('[Bluesky] Response already sent, ignoring close event');
                return;
            }
            
            if (code === 0) {
                try {
                    const cleanOutput = outputData.trim();
                    
                    if (!cleanOutput) {
                        console.error('❌ Bluesky Python output is empty');
                        return res.status(500).json({ error: 'Bluesky script produced no output. Check server logs.' });
                    }
                    
                    const result = JSON.parse(cleanOutput);
                    
                    if (result.success === false) {
                        console.error('❌ Bluesky script error:', result.error);
                        res.status(500).json({ error: result.error || 'Unknown Bluesky API error' });
                    } else {
                        console.log(`[Bluesky] Successfully retrieved ${result.totalPosts} posts for "${query}"`);
                        res.json(result);
                    }
                } catch (parseError) {
                    console.error('❌ Error parsing Bluesky output:', parseError.message);
                    console.error('Raw output (first 1000 chars):', outputData.substring(0, 1000));
                    res.status(500).json({ error: `Failed to parse Bluesky output: ${parseError.message}` });
                }
            } else {
                console.error('❌ Bluesky process failed with code:', code);
                console.error('Error output:', errorData);
                res.status(500).json({ error: `Bluesky search failed (exit code: ${code}). Error: ${errorData}` });
            }
        });
        
        pythonProcess.on('error', (error) => {
            clearTimeout(timeoutHandler);
            processFinished = true;
            
            console.error('❌ Failed to start Bluesky Python process:', error.message);
            if (!res.headersSent) {
                res.status(500).json({ error: `Failed to start Bluesky process: ${error.message}. Make sure Python is installed.` });
            }
        });
        
    } catch (error) {
        console.error('❌ Error in Bluesky endpoint:', error);
        if (!res.headersSent) {
            res.status(500).json({ error: `Server error: ${error.message}` });
        }
    }
});

// ===================================================================
// REDDIT API INTEGRATION
// ===================================================================
app.post('/api/reddit', async (req, res) => {
    console.log('[API Call] Received request for /api/reddit');
    const { query, limit } = req.body;

    if (!query || typeof query !== 'string' || query.trim().length === 0) {
        return res.status(400).json({ error: 'Search query is required and must be a non-empty string.' });
    }

    try {
        const searchLimit = Math.min(limit || 100, 100);
        console.log(`[Reddit] Searching for: "${query}" (limit: ${searchLimit})`);
        
        let pythonCommand = 'python3';
        
        try {
            require('child_process').execSync('python3 --version', { stdio: 'ignore' });
        } catch (e) {
            console.log('[Reddit] python3 not found, trying python...');
            pythonCommand = 'python';
        }
        
        console.log(`[Reddit] Using command: ${pythonCommand}`);
        
        const pythonProcess = spawn(pythonCommand, ['reddit_scraper.py', query, searchLimit.toString()], {
            cwd: __dirname,
            stdio: ['pipe', 'pipe', 'pipe'],
            timeout: 30000
        });
        
        let outputData = '';
        let errorData = '';
        let processFinished = false;
        
        const timeoutHandler = setTimeout(() => {
            if (!processFinished) {
                console.error('❌ Reddit Python process timed out');
                pythonProcess.kill('SIGKILL');
                if (!res.headersSent) {
                    res.status(500).json({ error: 'Reddit search timed out' });
                }
            }
        }, 30000);
        
        pythonProcess.stdout.on('data', (data) => {
            outputData += data.toString();
        });
        
        pythonProcess.stderr.on('data', (data) => {
            const errorText = data.toString();
            errorData += errorText;
            console.log(`[Reddit stderr]: ${errorText}`);
        });
        
        pythonProcess.on('close', (code) => {
            clearTimeout(timeoutHandler);
            processFinished = true;
            
            console.log(`[Reddit] Process exited with code: ${code}`);
            
            if (res.headersSent) {
                console.log('[Reddit] Response already sent, ignoring close event');
                return;
            }
            
            if (code === 0) {
                try {
                    const cleanOutput = outputData.trim();
                    
                    if (!cleanOutput) {
                        console.error('❌ Reddit Python output is empty');
                        return res.status(500).json({ error: 'Reddit script produced no output. Check server logs.' });
                    }
                    
                    const result = JSON.parse(cleanOutput);
                    
                    if (result.success === false) {
                        console.error('❌ Reddit script error:', result.error);
                        res.status(500).json({ error: result.error || 'Unknown Reddit API error' });
                    } else {
                        console.log(`[Reddit] Successfully retrieved ${result.totalPosts} posts for "${query}"`);
                        res.json(result);
                    }
                } catch (parseError) {
                    console.error('❌ Error parsing Reddit output:', parseError.message);
                    console.error('Raw output (first 1000 chars):', outputData.substring(0, 1000));
                    res.status(500).json({ error: `Failed to parse Reddit output: ${parseError.message}` });
                }
            } else {
                console.error('❌ Reddit process failed with code:', code);
                console.error('Error output:', errorData);
                res.status(500).json({ error: `Reddit search failed (exit code: ${code}). Error: ${errorData}` });
            }
        });
        
        pythonProcess.on('error', (error) => {
            clearTimeout(timeoutHandler);
            processFinished = true;
            
            console.error('❌ Failed to start Reddit Python process:', error.message);
            if (!res.headersSent) {
                res.status(500).json({ error: `Failed to start Reddit process: ${error.message}. Make sure Python is installed.` });
            }
        });
        
    } catch (error) {
        console.error('❌ Error in Reddit endpoint:', error);
        if (!res.headersSent) {
            res.status(500).json({ error: `Server error: ${error.message}` });
        }
    }
});

// ===================================================================
// US NATIONAL WEATHER SERVICE API INTEGRATION
// ===================================================================
app.post('/api/weather', async (req, res) => {
    console.log('[API Call] Received request for /api/weather');
    const { lat, lon } = req.body;

    try {
        console.log(`[Weather NWS] Getting weather data${lat && lon ? ` for coordinates (${lat}, ${lon})` : ' for current location'}`);
        
        let pythonCommand = 'python3';
        
        try {
            require('child_process').execSync('python3 --version', { stdio: 'ignore' });
        } catch (e) {
            console.log('[Weather NWS] python3 not found, trying python...');
            pythonCommand = 'python';
        }
        
        console.log(`[Weather NWS] Using command: ${pythonCommand}`);
        
        const args = ['nws_weather_service.py'];
        if (lat && lon) {
            args.push(lat.toString(), lon.toString());
        }
        
        const pythonProcess = spawn(pythonCommand, args, {
            cwd: __dirname,
            stdio: ['pipe', 'pipe', 'pipe'],
            timeout: 20000
        });
        
        let outputData = '';
        let errorData = '';
        let processFinished = false;
        
        const timeoutHandler = setTimeout(() => {
            if (!processFinished) {
                console.error('❌ Weather NWS Python process timed out');
                pythonProcess.kill('SIGKILL');
                if (!res.headersSent) {
                    res.status(500).json({ error: 'Weather service timed out' });
                }
            }
        }, 20000);
        
        pythonProcess.stdout.on('data', (data) => {
            outputData += data.toString();
        });
        
        pythonProcess.stderr.on('data', (data) => {
            const errorText = data.toString();
            errorData += errorText;
            console.log(`[Weather NWS stderr]: ${errorText}`);
        });
        
        pythonProcess.on('close', (code) => {
            clearTimeout(timeoutHandler);
            processFinished = true;
            
            console.log(`[Weather NWS] Process exited with code: ${code}`);
            
            if (res.headersSent) {
                console.log('[Weather NWS] Response already sent, ignoring close event');
                return;
            }
            
            if (code === 0) {
                try {
                    const cleanOutput = outputData.trim();
                    
                    if (!cleanOutput) {
                        console.error('❌ Weather NWS Python output is empty');
                        return res.status(500).json({ error: 'Weather script produced no output. Check server logs.' });
                    }
                    
                    const result = JSON.parse(cleanOutput);
                    
                    if (result.success === false) {
                        console.error('❌ Weather NWS script error:', result.error);
                        res.status(500).json({ error: result.error || 'Unknown weather API error' });
                    } else {
                        console.log(`[Weather NWS] Successfully retrieved weather data for ${result.location.city}, ${result.location.state}`);
                        res.json(result);
                    }
                } catch (parseError) {
                    console.error('❌ Error parsing weather NWS output:', parseError.message);
                    console.error('Raw output (first 1000 chars):', outputData.substring(0, 1000));
                    res.status(500).json({ error: `Failed to parse weather output: ${parseError.message}` });
                }
            } else {
                console.error('❌ Weather NWS process failed with code:', code);
                console.error('Error output:', errorData);
                res.status(500).json({ error: `Weather service failed (exit code: ${code}). Error: ${errorData}` });
            }
        });
        
        pythonProcess.on('error', (error) => {
            clearTimeout(timeoutHandler);
            processFinished = true;
            
            console.error('❌ Failed to start Weather NWS Python process:', error.message);
            if (!res.headersSent) {
                res.status(500).json({ error: `Failed to start weather process: ${error.message}. Make sure Python is installed.` });
            }
        });
        
    } catch (error) {
        console.error('❌ Error in weather NWS endpoint:', error);
        if (!res.headersSent) {
            res.status(500).json({ error: `Server error: ${error.message}` });
        }
    }
});

// ===================================================================
// UTILITY FUNCTIONS
// ===================================================================
function removeDuplicates(articles) {
    const seen = new Set();
    return articles.filter(article => {
        const key = `${article.title?.toLowerCase()}-${article.url}`;
        if (seen.has(key)) {
            return false;
        }
        seen.add(key);
        return true;
    });
}

function detectCategory(keyword) {
    const lowerKeyword = keyword.toLowerCase();
    
    if (lowerKeyword.includes('foreign') || lowerKeyword.includes('minister') || 
        lowerKeyword.includes('diplomacy') || lowerKeyword.includes('embassy')) {
        return 'ForeignMinisters';
    }
    if (lowerKeyword.includes('tech') || lowerKeyword.includes('ai') || 
        lowerKeyword.includes('software') || lowerKeyword.includes('computer')) {
        return 'technology';
    }
    if (lowerKeyword.includes('politic') || lowerKeyword.includes('election') || 
        lowerKeyword.includes('government') || lowerKeyword.includes('congress')) {
        return 'politics';
    }
    if (lowerKeyword.includes('business') || lowerKeyword.includes('economy') || 
        lowerKeyword.includes('market') || lowerKeyword.includes('finance')) {
        return 'business';
    }
    if (lowerKeyword.includes('world') || lowerKeyword.includes('international') || 
        lowerKeyword.includes('global') || lowerKeyword.includes('conflict')) {
        return 'world';
    }
    
    return 'ForeignMinisters';
}

function getDomain(url) {
    try {
        return new URL(url).hostname;
    } catch (error) {
        return 'unknown-domain';
    }
}

function generateRecentMockNews(keyword, maxResults) {
    const mockArticles = [];
    const sources = ['Reuters', 'BBC', 'Al Jazeera', 'Associated Press', 'CNN'];
    
    for (let i = 0; i < Math.min(maxResults, 10); i++) {
        const source = sources[i % sources.length];
        const publishedAt = new Date(Date.now() - (i * 2 * 60 * 60 * 1000));
        
        mockArticles.push({
            title: `${keyword} - Latest Development ${i + 1}`,
            description: `Recent news about ${keyword} from our ${source} correspondent. This is sample content while we resolve API issues.`,
            url: `https://example.com/news/${keyword.toLowerCase().replace(/\s+/g, '-')}-${i + 1}`,
            urlToImage: `https://via.placeholder.com/400x200?text=${source}+News`,
            publishedAt: publishedAt.toISOString(),
            source: {
                name: source,
                url: source.toLowerCase().replace(/\s+/g, '') + '.com',
                type: 'Mock Data (Fallback)'
            }
        });
    }
    
    return {
        totalArticles: mockArticles.length,
        articles: mockArticles,
        sources: ['Mock Data (Fallback)'],
        searchTerm: keyword,
        timestamp: new Date().toISOString(),
        note: 'This is sample data. API services are currently unavailable.'
    };
}

function extractPublishedDate($container, siteName, articleUrl) {
    const now = new Date();
    const dateSelectors = {
        'aljazeera.com': [
            { selector: 'time[datetime]', attribute: 'datetime' },
            { selector: '.gc__date time', attribute: 'datetime' },
            { selector: '.gc__date', text: true }
        ],
        'techcrunch.com': [
            { selector: 'time[datetime]', attribute: 'datetime' },
            { selector: '.post-block__meta time', text: true }
        ],
        'bbc.com': [
            { selector: 'time[datetime]', attribute: 'datetime' },
            { selector: '[data-testid="card-metadata-lastupdated"]', text: true }
        ]
    };
    
    const siteSpecificSelectors = dateSelectors[siteName] || [];
    const genericSelectors = [
        { selector: 'time[datetime]', attribute: 'datetime' },
        { selector: '.date', text: true },
        { selector: 'time', text: true }
    ];

    const allSelectorsToTry = [...siteSpecificSelectors, ...genericSelectors];

    for (const selObj of allSelectorsToTry) {
        const dateElement = $container.find(selObj.selector).first();
        if (dateElement.length > 0) {
            let dateStr = selObj.attribute ? dateElement.attr(selObj.attribute) : dateElement.text().trim();
            
            if (dateStr) {
                let cleanedDateStr = dateStr.replace(/(Published\s*(on)?|Updated|Last update on|ET|\s*\|.*)/gi, '').trim();
                const parsed = new Date(cleanedDateStr);
                if (!isNaN(parsed.getTime()) && parsed < now && parsed > new Date('2010-01-01')) {
                    return parsed.toISOString();
                }
            }
        }
    }
    
    return now.toISOString();
}

function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(String(email).toLowerCase());
}

// ===================================================================
// NEWSLETTER SIGNUP ENDPOINT
// ===================================================================
app.post('/api/newsletter/signup', (req, res) => {
    const { email } = req.body;
    
    if (!email || !validateEmail(email)) {
        return res.status(400).json({ error: 'Invalid email address.' });
    }
    
    console.log(`📬 New newsletter signup: ${email}`);
    res.json({ message: 'Thank you for signing up for our newsletter!' });
});

// ===================================================================
// STATIC FILE SERVING
// ===================================================================
app.use(express.static('.', {
    setHeaders: (res, filePath) => {
        if (filePath.endsWith('.html')) res.setHeader('Content-Type', 'text/html');
        else if (filePath.endsWith('.css')) res.setHeader('Content-Type', 'text/css');
        else if (filePath.endsWith('.js')) res.setHeader('Content-Type', 'application/javascript');
    }
}));

app.get('/', (req, res) => { res.redirect('/news_dashboard.html'); });

// ===================================================================
// HEALTH CHECK ENDPOINTS & SERVER STARTUP/SHUTDOWN
// ===================================================================
app.get('/install-deps', (req, res) => {
    res.json({
        message: 'Run: npm install cheerio puppeteer',
        dependencies: ['cheerio', 'puppeteer']
    });
});

app.get('/health', (req, res) => { 
    res.json({ 
        status: 'OK', 
        message: 'Multi-source news scraper with weather integration running',
        features: ['GNews API', 'Web Scraping', 'Google News RSS', 'Guardian API', 'Bluesky', 'Reddit', 'US Weather Service'],
        timestamp: new Date().toISOString()
    }); 
});

const PORT = process.env.PORT || 3000;
const server = app.listen(PORT, () => {
    console.log(`🚀 Multi-source news scraper with weather running on http://localhost:${PORT}`);
    console.log(`📡 Sources: GNews API + Web Scraping + Google News RSS + Guardian API + Social Media + Weather`);
    console.log(`🌦️ Weather: US National Weather Service integration active`);
    console.log('Press Ctrl+C to stop the server');
});

process.on('SIGINT', () => {
    console.log('\n🛑 Received SIGINT. Graceful shutdown...');
    server.close(() => {
        console.log('✅ HTTP server closed.');
        process.exit(0);
    });
});

process.on('SIGTERM', () => {
    console.log('\n🛑 Received SIGTERM. Graceful shutdown...');
    server.close(() => {
        console.log('✅ HTTP server closed.');
        process.exit(0);
    });
});