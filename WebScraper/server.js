// ===================================================================
// DEPENDENCIES AND SETUP
// ===================================================================
const express = require('express');
const cors = require('cors');
const fetch = require('node-fetch');
const cheerio = require('cheerio'); // For parsing HTML from static sites
const puppeteer = require('puppeteer'); // For scraping dynamic sites that use JavaScript
const { spawn } = require('child_process'); // Add this import
const fs = require('fs'); // Add this import
const path = require('path'); // Add this import

const app = express();
app.use(cors()); // Allow cross-origin requests
app.use(express.json()); // Parse JSON request bodies

// API key for GNews service (external news API)
const GNEWS_API_KEY = 'dac11b1cf0731071bb89fbfca20fbadf';

// ===================================================================
// AI SUMMARIZATION (NEW)
// ===================================================================
// Get your Google AI API Key here: https://aistudio.google.com/app/apikey
// It's highly recommended to use environment variables for API keys.
const GEMINI_API_KEY = process.env.GEMINI_API_KEY || "YOUR_GEMINI_API_KEY_HERE"; // IMPORTANT: Replace with your actual key

let genAI;
if (GEMINI_API_KEY && GEMINI_API_KEY !== "YOUR_GEMINI_API_KEY_HERE") {
    genAI = new GoogleGenerativeAI(GEMINI_API_KEY);
} else {
    console.warn('⚠️ WARNING: Gemini API key is not set or is a placeholder. Summarization will not work. Please set the GEMINI_API_KEY environment variable or update server.js.');
}

app.post('/api/summarize', async (req, res) => {
    console.log('[API Call] Received request for /api/summarize');
    const { articles, prompt } = req.body;

    if (!articles || !Array.isArray(articles) || articles.length === 0) {
        return res.status(400).json({ error: 'No articles provided for summarization or articles is not an array.' });
    }

    try {
        console.log(`[Python AI] Sending ${articles.length} articles to Python summarizer...`);
        
        // Limit articles to prevent overwhelming the summarizer
        const limitedArticles = articles.slice(0, 50); // Take exactly 50 most relevant
        console.log(`[Python AI] Limited to ${limitedArticles.length} articles for processing`);
        
        // Clean articles to remove problematic characters
        const cleanedArticles = limitedArticles.map(article => {
            if (typeof article === 'string') {
                // Remove control characters and clean the string
                return article
                    .replace(/[\x00-\x1F\x7F-\x9F]/g, ' ') // Remove control characters
                    .replace(/\s+/g, ' ') // Normalize whitespace
                    .trim();
            }
            return article;
        });
        
        // Prepare data for Python script with proper escaping
        const inputData = {
            articles: cleanedArticles,
            prompt: prompt || "Create a comprehensive global situation update from these news articles."
        };
        
        // Convert to JSON string with proper escaping
        const jsonString = JSON.stringify(inputData);
        console.log(`[Python AI] JSON string length: ${jsonString.length}`);
        
        // Try python3 first, then python as fallback
        let pythonCommand = 'python3';
        
        // Test if python3 exists
        try {
            require('child_process').execSync('python3 --version', { stdio: 'ignore' });
        } catch (e) {
            console.log('[Python AI] python3 not found, trying python...');
            pythonCommand = 'python';
        }
        
        console.log(`[Python AI] Using command: ${pythonCommand}`);
        
        // Write JSON to a temporary file instead of passing as argument
        const tempFilePath = path.join(__dirname, `temp_input_${Date.now()}.json`);
        
        try {
            fs.writeFileSync(tempFilePath, jsonString, 'utf8');
            console.log(`[Python AI] Wrote input to temporary file: ${tempFilePath}`);
            
            // Use the simple summarizer script (without transformers dependency)
            const scriptName = 'simple_news_summarizer.py';
            
            // Spawn Python process with file input
            const pythonProcess = spawn(pythonCommand, [scriptName, tempFilePath], {
                cwd: __dirname,
                stdio: ['pipe', 'pipe', 'pipe'],
                timeout: 60000 // 1 minute timeout (much shorter)
            });
            
            let outputData = '';
            let errorData = '';
            let processFinished = false;
            
            // Set up timeout handler
            const timeoutHandler = setTimeout(() => {
                if (!processFinished) {
                    console.error('❌ Python process timed out');
                    pythonProcess.kill('SIGKILL');
                    if (!res.headersSent) {
                        res.status(500).json({ error: 'Python summarizer timed out' });
                    }
                }
            }, 60000);
            
            pythonProcess.stdout.on('data', (data) => {
                outputData += data.toString();
            });
            
            pythonProcess.stderr.on('data', (data) => {
                const errorText = data.toString();
                errorData += errorText;
                if (errorText.includes('Error') || errorText.includes('Exception')) {
                    console.error(`[Python stderr ERROR]: ${errorText}`);
                } else {
                    console.log(`[Python stderr INFO]: ${errorText}`);
                }
            });
            
            pythonProcess.on('close', (code) => {
                clearTimeout(timeoutHandler);
                processFinished = true;
                
                // Clean up temporary file
                try {
                    fs.unlinkSync(tempFilePath);
                    console.log(`[Python AI] Cleaned up temporary file: ${tempFilePath}`);
                } catch (cleanupError) {
                    console.error(`[Python AI] Warning: Could not delete temp file: ${cleanupError.message}`);
                }
                
                console.log(`[Python] Process exited with code: ${code}`);
                console.log(`[Python] Output length: ${outputData.length}, Error length: ${errorData.length}`);
                
                if (res.headersSent) {
                    console.log('[Python] Response already sent, ignoring close event');
                    return;
                }
                
                if (code === 0) {
                    try {
                        const cleanOutput = outputData.trim();
                        
                        if (!cleanOutput) {
                            console.error('❌ Python output is empty');
                            console.error('Error data:', errorData);
                            return res.status(500).json({ error: 'Python script produced no output. Check server logs.' });
                        }
                        
                        console.log(`[Python] Raw output preview: ${cleanOutput.substring(0, 200)}...`);
                        
                        const result = JSON.parse(cleanOutput);
                        
                        if (result.error) {
                            console.error('❌ Python summarizer error:', result.error);
                            res.status(500).json({ error: result.error });
                        } else if (result.summary) {
                            console.log('[Python AI] Successfully received summary from Python.');
                            res.json({ summary: result.summary });
                        } else {
                            console.error('❌ Python output missing summary field');
                            res.status(500).json({ error: 'Invalid response format from summarizer' });
                        }
                    } catch (parseError) {
                        console.error('❌ Error parsing Python output:', parseError.message);
                        console.error('Raw output (first 1000 chars):', outputData.substring(0, 1000));
                        console.error('Error data:', errorData);
                        res.status(500).json({ error: `Failed to parse summarizer output: ${parseError.message}` });
                    }
                } else {
                    console.error('❌ Python process failed with code:', code);
                    console.error('Error output:', errorData);
                    res.status(500).json({ error: `Python summarizer process failed (exit code: ${code}). Error: ${errorData}` });
                }
            });
            
            pythonProcess.on('error', (error) => {
                clearTimeout(timeoutHandler);
                processFinished = true;
                
                // Clean up temporary file
                try {
                    fs.unlinkSync(tempFilePath);
                } catch (cleanupError) {
                    console.error(`[Python AI] Warning: Could not delete temp file: ${cleanupError.message}`);
                }
                
                console.error('❌ Failed to start Python process:', error.message);
                if (!res.headersSent) {
                    res.status(500).json({ error: `Failed to start Python process: ${error.message}. Make sure Python is installed and accessible.` });
                }
            });
            
        } catch (fileError) {
            console.error('❌ Error writing temporary file:', fileError.message);
            res.status(500).json({ error: `Failed to prepare input data: ${fileError.message}` });
        }
        
    } catch (error) {
        console.error('❌ Error in summarize endpoint:', error);
        if (!res.headersSent) {
            res.status(500).json({ error: `Server error: ${error.message}` });
        }
    }
});

// ===================================================================
// SITE-SPECIFIC SCRAPER CONFIGURATION
// ===================================================================
// This object defines how to scrape each specific news website
// Each site has unique HTML structure, so needs its own selectors
const SCRAPER_CONFIG = {
    'techcrunch.com': {
        isDynamic: false, // Static site - can use fast Cheerio scraping
        selectors: {
            container: 'div.post-block, article.post-block', // Where articles are contained
            title: 'a.post-block__title__link, h2.post-block__title a', // How to find article titles
            link: 'a.post-block__title__link, h2.post-block__title a', // How to find article URLs
            excerpt: 'div.post-block__content, .post-block__excerpt' // How to find article descriptions
        }
    },
    'aljazeera.com': {
        isDynamic: true, // Dynamic site - requires Puppeteer (slower but can handle JavaScript)
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
            container: '.athing', // Hacker News uses simple class names
            title: '.titleline > a',
            link: '.titleline > a',
            excerpt: '' // Hacker News doesn't have excerpts
        }
    },
    // COMMENTED OUT THEVERGE.COM DUE TO TIMEOUT ISSUES
    // 'theverge.com': {
    //     isDynamic: true, // The Verge loads content dynamically
    //     selectors: {
    //         container: 'article, .c-entry-box',
    //         title: 'h2 a, .c-entry-box__title a',
    //         link: 'h2 a, .c-entry-box__title a',
    //         excerpt: '.c-entry-summary, .summary'
    //     }
    // },
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
        isDynamic: true, // Reuters uses React/JavaScript for content loading
        selectors: {
            container: '[data-testid="MediaStoryCard"], article',
            title: '[data-testid="Heading"], h3 a',
            link: 'a',
            excerpt: '[data-testid="Body"], .summary'
        }
    },
    'apnews.com': {
        isDynamic: true, // AP News search results load dynamically
        selectors: {
            container: 'div.Card, .SearchResultsModule-results div',
            title: 'h3, .CardHeadline',
            link: 'a.Link, a',
            excerpt: 'div.CardContent, .summary'
        }
    },
    'bloomberg.com': {
        isDynamic: true, // Bloomberg heavily uses JavaScript
        selectors: {
            container: 'article, .story-package-module__story',
            title: 'h3 a, .headline',
            link: 'a',
            excerpt: '.summary, .abstract'
        }
    },
    'bbc.com': {
        isDynamic: false, // BBC has good static HTML structure
        selectors: {
            container: '[data-testid="card"], .media__content',
            title: '[data-testid="card-headline"], h3 a',
            link: 'a',
            excerpt: '[data-testid="card-description"], .media__summary'
        }
    },
    'dw.com': {
        isDynamic: false, // Deutsche Welle has static structure
        selectors: {
            container: '.searchResult, article',
            title: '.searchResult h2 a, h2 a',
            link: '.searchResult h2 a, h2 a',
            excerpt: '.searchResult .intro, .summary'
        }
    },
    'findit.state.gov': {
        isDynamic: false, // US State Department search is static
        selectors: {
            container: '.result, .search-result',
            title: '.result-title a, h3 a',
            link: '.result-title a, h3 a',
            excerpt: '.result-desc, .summary'
        }
    },
    'duckduckgo.com': {
        isDynamic: true, // DuckDuckGo loads results dynamically
        selectors: {
            container: 'article.result, .result',
            title: 'h2 a, .result__title a',
            link: 'h2 a, .result__title a',
            excerpt: '.result__snippet, .summary'
        }
    }
};

// ===================================================================
// NEWS SOURCE CATEGORIES
// ===================================================================
// This organizes news sources by topic/category
// Each category has different sources that are most relevant
const NEWS_SOURCES = {
    technology: [
        { url: 'https://techcrunch.com/search/{keyword}/', scraperKey: 'techcrunch.com' },
        { url: 'https://www.aljazeera.com/search/{keyword}', scraperKey: 'aljazeera.com' },
        { url: 'https://arstechnica.com/search/?query={keyword}', scraperKey: 'arstechnica.com' },
        { url: 'https://news.ycombinator.com/search?q={keyword}', scraperKey: 'news.ycombinator.com' }
    ],
    ForeignMinisters: [ // Special category for diplomatic news - REMOVED THEVERGE.COM
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
        { url: 'https://www.bloomberg.com/search?query={keyword}', scraperKey: 'bloomberg.com' },
        { url: 'https://finance.yahoo.com/search?p={keyword}', scraperKey: 'finance.yahoo.com' },
        { url: 'https://www.marketwatch.com/search?q={keyword}', scraperKey: 'marketwatch.com' }
    ],
    world: [ // International news sources
        { url: 'https://www.bbc.com/search?q={keyword}', scraperKey: 'bbc.com' },
        { url: 'https://www.aljazeera.com/search/{keyword}', scraperKey: 'aljazeera.com' },
        { url: 'https://www.dw.com/search/?languageCode=en&item={keyword}', scraperKey: 'dw.com' }
    ]
};

// Fallback sources used when no specific category matches
const GENERIC_SOURCES = [
    { url: 'https://findit.state.gov/search?query={keyword}&affiliate=dos_stategov', scraperKey: 'findit.state.gov' },
    { url: 'https://duckduckgo.com/?q={keyword}+news&t=h_&iar=news', scraperKey: 'duckduckgo.com' }
];

// ===================================================================
// MAIN API ENDPOINT
// ===================================================================
// This is the main endpoint that clients call to get news articles
app.get('/api/news', async (req, res) => {
    try {
        // Extract parameters from the request
        const { q, lang, country, max } = req.query;
        const keyword = q || 'technology'; // Default search term
        const maxResults = parseInt(max) || 10; // How many articles to return
        const articlesToFetchPerSource = Math.max(maxResults * 2, 20); // Fetch extra for deduplication

        console.log(`\n🔍 Searching for "${keyword}" (target: ${maxResults} most recent) from ALL sources...`);
        
        let allArticles = []; // Will collect all articles from all sources
        
        // ===================================================================
        // SOURCE 1: GNEWS API (EXTERNAL PAID SERVICE)
        // ===================================================================
        console.log(`[API_CALL] Attempting GNews API for "${keyword}"...`);
        try {
            const gnewsData = await fetchFromGNews(keyword, lang, country, articlesToFetchPerSource);
            if (gnewsData && gnewsData.articles && gnewsData.articles.length > 0) {
                // Add source type to each article for tracking
                const gnewsArticles = gnewsData.articles.map(article => ({
                    ...article,
                    source: { ...article.source, type: 'GNews API' }
                }));
                allArticles.push(...gnewsArticles);
                console.log(`  ✅ GNews API: Fetched ${gnewsData.articles.length} articles for "${keyword}".`);
            } else {
                console.log(`  ℹ️ GNews API: No articles found for "${keyword}".`);
            }
        } catch (gnewsError) {
            console.log(`  ❌ GNews API failed for "${keyword}":`, gnewsError.message);
        }
        
        // ===================================================================
        // SOURCE 2: WEB SCRAPING (DIRECT FROM NEWS SITES)
        // ===================================================================
        console.log(`[API_CALL] Attempting Web Scraping for "${keyword}"...`);
        try {
            const scrapedArticles = await scrapeNewsFromSources(keyword, articlesToFetchPerSource);
            if (scrapedArticles.length > 0) {
                allArticles.push(...scrapedArticles);
                console.log(`  ✅ Web Scraping: Fetched ${scrapedArticles.length} articles for "${keyword}".`);
            } else {
                console.log(`  ℹ️ Web Scraping: No articles found for "${keyword}".`);
            }
        } catch (scrapeError) {
            console.log(`  ❌ Web Scraping failed for "${keyword}":`, scrapeError.message);
        }
        
        // ===================================================================
        // SOURCE 3: GOOGLE NEWS RSS FEED
        // ===================================================================
        console.log(`[API_CALL] Attempting Google News RSS for "${keyword}"...`);
        try {
            const googleNewsArticles = await scrapeGoogleNews(keyword, articlesToFetchPerSource);
            if (googleNewsArticles.length > 0) {
                allArticles.push(...googleNewsArticles);
                console.log(`  ✅ Google News RSS: Fetched ${googleNewsArticles.length} articles for "${keyword}".`);
            } else {
                console.log(`  ℹ️ Google News RSS: No articles found for "${keyword}".`);
            }
        } catch (googleError) {
            console.log(`  ❌ Google News RSS failed for "${keyword}":`, googleError.message);
        }
        
        // ===================================================================
        // PROCESS AND RETURN RESULTS
        // ===================================================================
        console.log(`[PROCESSING] Total articles collected before deduplication: ${allArticles.length} for "${keyword}".`);

        // Remove duplicate articles (same title or URL)
        const uniqueArticles = removeDuplicates(allArticles);
        console.log(`[PROCESSING] Articles after deduplication: ${uniqueArticles.length} for "${keyword}".`);

        // Sort by date (newest first) and limit to requested number
        const sortedArticles = uniqueArticles
            .filter(article => article.publishedAt) // Only articles with dates
            .sort((a, b) => new Date(b.publishedAt) - new Date(a.publishedAt)) // Newest first
            .slice(0, maxResults); // Limit to requested amount
        
        if (sortedArticles.length > 0) {
            // Prepare response with metadata
            const sourceTypes = [...new Set(sortedArticles.map(a => a.source.type))];
            console.log(`📰 Returning ${sortedArticles.length} most recent articles for "${keyword}".`);
            console.log(`📊 Sources used: [${sourceTypes.join(', ')}]`);
            
            // Log date range if we have multiple articles
            if (sortedArticles.length > 1) {
                console.log(`📅 Date range: ${new Date(sortedArticles[0].publishedAt).toLocaleString()} to ${new Date(sortedArticles[sortedArticles.length-1].publishedAt).toLocaleString()}`);
            }
            
            // Return successful response
            return res.json({
                totalArticles: sortedArticles.length,
                articles: sortedArticles,
                sources: sourceTypes,
                searchTerm: keyword,
                timestamp: new Date().toISOString()
            });
        } else {
            // No articles found - return mock data as fallback
            console.log(`📝 No articles found for "${keyword}" from any source. Using mock data as fallback.`);
            return res.json(generateRecentMockNews(keyword, maxResults));
        }
        
    } catch (error) {
        // Handle any unexpected errors
        console.error(`❌ Major error in /api/news for keyword "${req.query.q}":`, error);
        const maxResults = parseInt(req.query.max) || 10;
        res.status(500).json({ 
            error: error.message,
            articles: generateRecentMockNews(req.query.q || 'news', maxResults).articles
        });
    }
});

// ===================================================================
// WEB SCRAPING CONTROLLER FUNCTION
// ===================================================================
// This function coordinates scraping from multiple news websites
async function scrapeNewsFromSources(keyword, maxNeeded) {
    console.log(`  [Scraper] Initiated for keyword: "${keyword}"`);
    let browser = null; // Will hold Puppeteer browser instance
    
    try {
        const collectedArticles = [];
        
        // Determine which category of sources to use based on keyword
        const category = detectCategory(keyword);
        console.log(`    [Scraper] Detected category: "${category}" for keyword "${keyword}"`);
        
        // Get the appropriate sources for this category
        let sourcesToAttempt = NEWS_SOURCES[category];
        let sourceOrigin = `NEWS_SOURCES["${category}"]`;

        // If no category matches, use generic sources
        if (!sourcesToAttempt || sourcesToAttempt.length === 0) {
            sourcesToAttempt = GENERIC_SOURCES;
            sourceOrigin = 'GENERIC_SOURCES (fallback)';
        }
        
        console.log(`    [Scraper] Using ${sourceOrigin}. Will attempt ALL sites from this list.`);

        // Launch Puppeteer browser once to share across all dynamic sites (more efficient)
        browser = await puppeteer.launch({ 
            headless: 'new', // Run in background without UI
            args: ['--no-sandbox', '--disable-setuid-sandbox'] // Security flags for server environments
        });

        // Loop through each source and scrape it
        for (const source of sourcesToAttempt) {
            // Get the configuration for this specific website
            const config = SCRAPER_CONFIG[source.scraperKey];
            if (!config) {
                console.log(`      [Scraper] ⚠️ No config found for ${source.scraperKey}, skipping.`);
                continue;
            }

            // Replace {keyword} placeholder with actual search term
            const url = source.url.replace('{keyword}', encodeURIComponent(keyword));
            let siteArticles = [];

            try {
                // Choose scraping method based on whether site is dynamic or static
                if (config.isDynamic) {
                    console.log(`      [Scraper] -> Using Puppeteer for ${source.scraperKey}`);
                    siteArticles = await scrapeWithPuppeteerNew(browser, url, config.selectors, source.scraperKey);
                } else {
                    console.log(`      [Scraper] -> Using Cheerio for ${source.scraperKey}`);
                    siteArticles = await scrapeWithCheerio(url, config.selectors, source.scraperKey);
                }

                // Filter out invalid articles (like Al Jazeera tag pages)
                const validArticles = siteArticles.filter(article => {
                    if (!article.url || !article.title) return false;
                    
                    // Filter out Al Jazeera tag pages and category pages
                    if (article.url.includes('/tag/') || 
                        article.url.includes('/category/') ||
                        article.title.toLowerCase().includes('today\'s latest from al jazeera') ||
                        article.title.toLowerCase().includes('| today\'s latest from')) {
                        console.log(`        [Filter] Excluding tag/category page: ${article.title} (${article.url})`);
                        return false;
                    }
                    
                    return true;
                });

                // Add source information to each valid article
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
                    console.log(`        [Scraper] <- Fetched ${validArticles.length} valid articles from ${source.scraperKey} (filtered out ${siteArticles.length - validArticles.length} invalid)`);
                } else {
                    console.log(`        [Scraper] <- No valid articles found on ${source.scraperKey} (${siteArticles.length} total found but filtered out)`);
                }
            } catch (error) {
                console.error(`        [Scraper] XXX Error processing ${source.scraperKey}: ${error.message}`);
            }
        }
        
        console.log(`  [Scraper] Finished. Total collected for "${keyword}": ${collectedArticles.length}`);
        return collectedArticles;
        
    } finally {
        // Always close the browser to free up resources
        if (browser) {
            await browser.close();
            console.log(`    [Scraper] Browser closed.`);
        }
    }
}

// ===================================================================
// ENHANCED CHEERIO SCRAPER (FOR STATIC SITES)
// ===================================================================
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
                
                // Get title and link
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
                
                // Convert relative URL to absolute
                let fullUrl;
                try {
                    fullUrl = linkUrl.startsWith('http') ? linkUrl : new URL(linkUrl, new URL(url).origin).href;
                } catch (urlError) {
                    console.log(`            [Cheerio] Invalid URL "${linkUrl}" from ${siteName}`);
                    return true;
                }

                // ENHANCED FILTERING FOR AL JAZEERA TAG PAGES AND CATEGORY PAGES
                if (fullUrl.includes('/tag/') || 
                    fullUrl.includes('/category/') ||
                    title.toLowerCase().includes('today\'s latest from al jazeera') ||
                    title.toLowerCase().includes('| today\'s latest from') ||
                    title.toLowerCase().includes('conflict | today\'s latest') ||
                    fullUrl.includes('/tag/conflict/') ||
                    fullUrl.includes('/tag/foreign') ||
                    fullUrl.includes('/tag/minister') ||
                    fullUrl.includes('/tag/state') ||
                    fullUrl.includes('/category/')) {
                    console.log(`        [Filter] Excluding tag/category page: ${title} (${fullUrl})`);
                    return true; // Skip this article
                }
                
                // Get excerpt
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
                
                // EXTRACT ACTUAL PUBLICATION DATE
                let publishedAt = extractPublishedDate($container, siteName, fullUrl); // Pass URL for context
                
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

// ===================================================================
// ENHANCED PUPPETEER SCRAPER (FOR DYNAMIC SITES)
// ===================================================================
async function scrapeWithPuppeteerNew(browser, url, selectors, siteName) {
    console.log(`        [Puppeteer] Scraping ${siteName}: ${url.substring(0, 80)}...`);
    
    const page = await browser.newPage();
    await page.setUserAgent('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36');

    // Listen for console events from the page and pipe them to Node's console
    page.on('console', msg => {
        const type = msg.type();
        const text = msg.text();
        // Only log messages that we've intentionally put for debugging
        if (text.startsWith('[AlJazeera DateDebug]') || text.startsWith('[DateDebug Browser]')) {
            console.log(`          [Puppeteer Page Console - ${type.toUpperCase()}]: ${text}`);
        } else if (type === 'error' || type === 'warn') { // Log other errors/warnings from browser
            console.log(`          [Puppeteer Page Console - ${type.toUpperCase()}]: ${text}`);
        }
    });
    // Listen for page errors
    page.on('pageerror', error => {
        console.error(`          [Puppeteer Page Error]: ${error.message}`);
    });

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
                // console.log(`          [Puppeteer] Container selector "${containerSelector}" not found for ${siteName}, trying next...`); // Reduced verbosity
            }
        }
        
        if (!selectorFound) {
            console.log(`          [Puppeteer] No article container selectors found for ${siteName} at ${url}`);
            await page.close();
            return [];
        }
        
        // Enhanced JavaScript extraction with date parsing
        const articles = await page.evaluate((s, site, pageUrl) => { // Renamed params to avoid conflict
            const results = [];
            const nowEval = new Date(); // 'now' in browser context

            // Date extraction function for browser context
            function extractPublishedDateInBrowser(container, siteNameForDate, articleUrlForDate) {
                const now = new Date();
                let dateFound = false;

                // Common date selectors by site
                const dateSelectors = {
                    'aljazeera.com': [
                        { selector: 'time[datetime]', attribute: 'datetime' },
                        { selector: '.gc__date time', attribute: 'datetime' },
                        { selector: '.gc__date', text: true },
                        { selector: '.date-simple-format', text: true },
                        { selector: '[data-testid="article-date"]', text: true },
                        { selector: 'div[data-testid="card-metadata"] span:first-of-type', text: true },
                        { selector: '.u-clickable-card__date', text: true },
                        { selector: 'span.article-dates__published time', attribute: 'datetime'},
                        { selector: 'span.article-dates__published .screen-reader-text', text: true, parentText: 'span.article-dates__published'},
                        { selector: 'div.date-simple', text: true }
                    ],
                    'reuters.com': [
                        { selector: 'time[datetime]', attribute: 'datetime' },
                        { selector: '.ArticleHeader-date time', attribute: 'datetime' },
                        { selector: '.MediaStoryCard-publishedDate', text: true },
                        { selector: '[data-testid="published-timestamp"]', text: true }
                    ],
                    'apnews.com': [
                        { selector: 'time[data-source="ap"]', attribute: 'datetime' },
                        { selector: '.Timestamp', text: true },
                        { selector: '.Card-time', text: true },
                        { selector: 'time', text: true }
                    ],
                    'bloomberg.com': [
                        { selector: 'time[datetime]', attribute: 'datetime' },
                        { selector: '.Story-meta time', text: true },
                        { selector: '.article-timestamp', text: true }
                    ],
                    'theverge.com': [
                        { selector: 'time[datetime]', attribute: 'datetime' },
                        { selector: '.c-byline__item time', text: true },
                        { selector: '.relative', text: true }
                    ]
                };
                
                const siteSpecificSelectors = dateSelectors[siteNameForDate] || [];
                const genericSelectors = [
                    { selector: 'time[datetime]', attribute: 'datetime' },
                    { selector: 'meta[property="article:published_time"]', attribute: 'content' },
                    { selector: 'meta[name="pubdate"]', attribute: 'content' },
                    { selector: 'meta[name="parsely-pub-date"]', attribute: 'content' },
                    { selector: '.date', text: true },
                    { selector: '.timestamp', text: true },
                    { selector: 'time', text: true }
                ];

                const allSelectorsToTry = [...siteSpecificSelectors, ...genericSelectors];
                
                if (siteNameForDate === 'aljazeera.com') {
                    console.log(`[AlJazeera DateDebug] Trying to extract date for article (URL: ${articleUrlForDate}) in container:`, container.innerHTML.substring(0, 350));
                }

                for (const selObj of allSelectorsToTry) {
                    let dateElement = container.querySelector(selObj.selector);
                    let dateStr = null;

                    if (dateElement) {
                        if (selObj.attribute) {
                            dateStr = dateElement.getAttribute(selObj.attribute);
                        } else if (selObj.text) {
                            if (selObj.parentText && container.querySelector(selObj.parentText)) {
                                const parentElement = container.querySelector(selObj.parentText);
                                const childTextElement = parentElement ? parentElement.querySelector(selObj.selector) : null;
                                dateStr = childTextElement ? childTextElement.textContent?.trim() : parentElement?.textContent?.trim();
                            } else {
                                dateStr = dateElement.textContent?.trim();
                            }
                        }
                    }
                        
                    if (siteNameForDate === 'aljazeera.com') {
                        console.log(`[AlJazeera DateDebug] Selector: "${selObj.selector}", Found element: ${!!dateElement}, Raw dateStr: "${dateStr}"`);
                    }

                    if (dateStr) {
                        // Handle duplicated text first (Al Jazeera specific issue)
                        let cleanedDateStr = dateStr;
                        
                        // Fix duplicated text like "Last update 12 Jun 2025Last update 12 Jun 2025"
                        const duplicatePattern = /^(.+?)\1+$/; // Matches if string repeats itself
                        if (duplicatePattern.test(cleanedDateStr)) {
                            // Take only the first half if string is duplicated
                            cleanedDateStr = cleanedDateStr.substring(0, cleanedDateStr.length / 2);
                            if (siteNameForDate === 'aljazeera.com') {
                                console.log(`[AlJazeera DateDebug] Detected duplicated text, using first half: "${cleanedDateStr}"`);
                            }
                        }
                        
                        // Now clean the date string
                        cleanedDateStr = cleanedDateStr.replace(/(Published\s*(on)?|Updated|Last update(\s+on)?)\s*/gi, '').trim();
                        cleanedDateStr = cleanedDateStr.replace(/\b[A-Z]{3,5}\b(?!.*\d{4})/g, '').trim();
                        cleanedDateStr = cleanedDateStr.replace(/(\d+)(st|nd|rd|th)/g, '$1');
                        cleanedDateStr = cleanedDateStr.replace(/\bSept\b/i, 'Sep');
                        
                        // Handle specific Al Jazeera date formats
                        if (siteNameForDate === 'aljazeera.com') {
                            // Convert "12 Jun 2025" to "Jun 12, 2025" format for better parsing
                            const dateMatch = cleanedDateStr.match(/(\d{1,2})\s+([A-Za-z]{3,9})\s+(\d{4})/);
                            if (dateMatch) {
                                const [, day, month, year] = dateMatch;
                                cleanedDateStr = `${month} ${day}, ${year}`;
                                console.log(`[AlJazeera DateDebug] Reformatted Al Jazeera date: "${cleanedDateStr}"`);
                            }
                        }

                        if (siteNameForDate === 'aljazeera.com') {
                            console.log(`[AlJazeera DateDebug] Final cleaned dateStr: "${cleanedDateStr}"`);
                        }
                        
                        const parsed = new Date(cleanedDateStr);
                        if (!isNaN(parsed.getTime()) && parsed < now && parsed > new Date('2010-01-01')) {
                            if (siteNameForDate === 'aljazeera.com') {
                                console.log(`[AlJazeera DateDebug] Successfully parsed date: ${parsed.toISOString()} from "${cleanedDateStr}"`);
                            }
                            dateFound = true;
                            return parsed.toISOString();
                        } else if (siteNameForDate === 'aljazeera.com') {
                            console.log(`[AlJazeera DateDebug] Failed to parse date string "${cleanedDateStr}" into valid date. Parsed: ${parsed}`);
                        }
                        
                        // Try relative date parsing as before...
                        const relativeMatch = cleanedDateStr.match(/(\d+)\s*(minute|min|hour|hr|day|week|month)s?\s*ago/i);
                        if (relativeMatch) {
                            const amount = parseInt(relativeMatch[1]);
                            const unit = relativeMatch[2].toLowerCase();
                            let milliseconds = 0;
                            
                            switch (unit) {
                                case 'minute': case 'min': milliseconds = amount * 60 * 1000; break;
                                case 'hour': case 'hr': milliseconds = amount * 60 * 60 * 1000; break;
                                case 'day': milliseconds = amount * 24 * 60 * 60 * 1000; break;
                                case 'week': milliseconds = amount * 7 * 24 * 60 * 60 * 1000; break;
                                case 'month': milliseconds = amount * 30 * 24 * 60 * 60 * 1000; break;
                            }
                            
                            if (milliseconds > 0) {
                                const calculatedDate = new Date(now.getTime() - milliseconds);
                                if (siteNameForDate === 'aljazeera.com') {
                                    console.log(`[AlJazeera DateDebug] Parsed relative date: "${cleanedDateStr}" -> ${calculatedDate.toISOString()}`);
                                }
                                dateFound = true;
                                return calculatedDate.toISOString();
                            }
                        }
                    }
                }
                
                if (siteNameForDate === 'aljazeera.com' && !dateFound) {
                    console.warn(`[AlJazeera DateDebug] ⚠️ No valid date found for Al Jazeera article. URL: ${articleUrlForDate}. Using fallback. Container HTML snippet:`, container.innerHTML.substring(0, 500));
                }
                return now.toISOString(); // Fallback
            }

            // Main part of page.evaluate
            const containerSelectorsEval = s.container.split(',').map(cs => cs.trim()); // Renamed
            for (const containerSelector of containerSelectorsEval) {
                const containers = document.querySelectorAll(containerSelector);
                if (containers.length > 0) {
                    containers.forEach((container) => {
                        if (results.length >= 5) return; // Limit articles per site

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

                        // ENHANCED FILTERING FOR AL JAZEERA TAG PAGES AND CATEGORY PAGES
                        if (link.includes('/tag/') || 
                            link.includes('/category/') ||
                            title.toLowerCase().includes('today\'s latest from al jazeera') ||
                            title.toLowerCase().includes('| today\'s latest from') ||
                            title.toLowerCase().includes('conflict | today\'s latest') ||
                            link.includes('/tag/conflict/') ||
                            link.includes('/tag/foreign') ||
                            link.includes('/tag/minister') ||
                            link.includes('/tag/state') ||
                            link.includes('/category/')) {
                            console.log(`[Filter] Excluding tag/category page: ${title} (${link})`);
                            return; // Skip this article
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
                        
                        const publishedAt = extractPublishedDateInBrowser(container, site, link);
                        
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
        }, selectors, siteName, url); // Pass `selectors`, `siteName`, `url` as arguments to page.evaluate

        console.log(`          [Puppeteer] Finished ${siteName}. Found ${articles.length} articles.`);
        await page.close();
        return articles;
        
    } catch (error) {
        console.error(`          [Puppeteer] Error scraping ${siteName} at ${url}: ${error.message}`);
        if (page && !page.isClosed()) {
            await page.close();
        }
        return []; // Return empty array on error
    }
}

// ===================================================================
// GNEWS API FUNCTION
// ===================================================================
// This function calls the external GNews API service
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

// ===================================================================
// GOOGLE NEWS RSS SCRAPER
// ===================================================================
// This function scrapes Google News RSS feed (XML format)
async function scrapeGoogleNews(keyword, maxResults) {
    try {
        const url = `https://news.google.com/rss/search?q=${encodeURIComponent(keyword)}&hl=en&gl=US&ceid=US:en`;
        
        const response = await fetch(url, {
            headers: {
                'User-Agent': 'Mozilla/5.0 (compatible; NewsBot/1.0)'
            }
        });
        
        const xmlText = await response.text();
        const $ = cheerio.load(xmlText, { xmlMode: true }); // Parse XML
        const articles = [];
        
        // Extract data from each RSS item
        $('item').each((i, element) => {
            if (i >= maxResults) return false; // Limit results
            
            const $item = $(element);
            const title = $item.find('title').text();
            const link = $item.find('link').text();
            const description = $item.find('description').text().replace(/<[^>]*>/g, ''); // Remove HTML tags
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

// ===================================================================
// UTILITY FUNCTIONS
// ===================================================================

// Determines which category of news sources to use based on search keyword
function detectCategory(keyword) {
    const lowerKeyword = keyword.toLowerCase();
    if (['technology', 'tech', 'ai', 'software', 'computer', 'digital'].some(k => lowerKeyword.includes(k))) return 'technology';
    if (['foreign minister', 'department of state', 'diplomacy'].some(k => lowerKeyword.includes(k))) return 'ForeignMinisters';
    if (['politics', 'government', 'election', 'policy', 'minister', 'state'].some(k => lowerKeyword.includes(k))) return 'politics';
    if (['business', 'finance', 'market', 'economy', 'stock'].some(k => lowerKeyword.includes(k))) return 'business';
    
    return 'world'; // Default category
}

// Helper function to extract description from article (not currently used but kept for future)
function extractDescription($, linkElement) {
    const parent = $(linkElement).closest('article, .story, .entry');
    const description = parent.find('p, .summary, .excerpt, .description').first().text().trim();
    return description.length > 20 ? description.substring(0, 200) + '...' : null;
}

// Extracts domain name from URL for source identification
function getDomain(url) {
    try {
        return new URL(url).hostname.replace('www.', '');
    } catch {
        return 'Unknown Source';
    }
}

// Removes duplicate articles based on title similarity and URL
function removeDuplicates(articles) {
    const seen = new Set(); // For tracking title similarities
    const urlsSeen = new Set(); // For tracking exact URL matches
    
    return articles.filter(article => {
        // Create a simplified version of the title for comparison
        const titleKey = article.title.toLowerCase()
            .replace(/[^\w\s]/g, '') // Remove punctuation
            .replace(/\s+/g, ' ') // Normalize spaces
            .substring(0, 60); // Use first 60 characters
        
        const urlKey = article.url ? article.url.toLowerCase() : '';
        
        // Skip if we've seen this title or URL before
        if (seen.has(titleKey) || urlsSeen.has(urlKey)) {
            return false;
        }
        
        // Track this title and URL
        seen.add(titleKey);
        if (urlKey) urlsSeen.add(urlKey);
        return true;
    });
}

// Generates fake news articles when no real articles are found (fallback)
function generateRecentMockNews(keyword, maxResults) {
    maxResults = maxResults || 10;
    const now = new Date();
    const articles = [];
    
    for (let i = 0; i < maxResults; i++) {
        // Create articles with realistic timestamps (spread over last few hours)
        const minutesAgo = Math.floor(Math.random() * 180) + 15 + (i * 10);
        const publishedAt = new Date(now.getTime() - (minutesAgo * 60 * 1000));
        
        articles.push({
            title: `Breaking: ${keyword} developments from multiple sources - Update ${i + 1}`,
            description: `Comprehensive coverage of ${keyword} from various news outlets and web sources.`,
            url: `https://example.com/news/${keyword.toLowerCase().replace(/\s+/g, '-')}-${Date.now()}-${i}`,
            urlToImage: null,
            publishedAt: publishedAt.toISOString(),
            source: {
                name: `Multi-Source ${keyword.charAt(0).toUpperCase() + keyword.slice(1)}`,
                url: "https://example.com",
                type: 'Mock Data'
            }
        });
    }
    
    return {
        totalResults: articles.length,
        articles: articles,
        sources: ['Mock Data'],
        searchTerm: keyword,
        timestamp: new Date().toISOString()
    };
}

// ===================================================================
// HEALTH CHECK ENDPOINTS
// ===================================================================

// Endpoint to check required dependencies
app.get('/install-deps', (req, res) => {
    res.json({
        message: 'Run: npm install cheerio puppeteer',
        dependencies: ['cheerio', 'puppeteer']
    });
});

// Basic health check endpoint
app.get('/health', (req, res) => {
    res.json({ status: 'OK', message: 'Refactored multi-source news scraper running' });
});

// ===================================================================
// SERVER STARTUP AND SHUTDOWN HANDLING
// ===================================================================

const PORT = process.env.PORT || 3000;
const server = app.listen(PORT, () => {
    console.log(`🚀 Refactored multi-source news scraper running on http://localhost:${PORT}`);
    console.log(`📡 Sources: GNews API + Site-Specific Web Scraping + Google News RSS`);
    console.log('Press Ctrl+C to stop the server');
});

// Handle graceful shutdown on Ctrl+C
process.on('SIGINT', () => {
    console.log('\n🛑 Received SIGINT. Graceful shutdown...');
    server.close(() => {
        console.log('✅ HTTP server closed.');
        process.exit(0);
    });
});

// Handle graceful shutdown on termination signal
process.on('SIGTERM', () => {
    console.log('\n🛑 Received SIGTERM. Graceful shutdown...');
    server.close(() => {
        console.log('✅ HTTP server closed.');
        process.exit(0);
    });
});

// ===================================================================
// DATE EXTRACTION UTILITY FUNCTION (for Cheerio)
// ===================================================================
function extractPublishedDate($container, siteName, articleUrl) {
    const now = new Date();
    let dateFound = false;

    const dateSelectors = {
        'aljazeera.com': [
            { selector: 'time[datetime]', attribute: 'datetime' },
            { selector: '.gc__date time', attribute: 'datetime' },
            { selector: '.gc__date', text: true },
            { selector: '.date-simple-format', text: true },
            { selector: '[data-testid="article-date"]', text: true },
            { selector: 'div[data-testid="card-metadata"] span:first-of-type', text: true },
            { selector: '.u-clickable-card__date', text: true },
            { selector: 'span.article-dates__published time', attribute: 'datetime'},
            { selector: 'span.article-dates__published .screen-reader-text', text: true, parentText: 'span.article-dates__published'},
            { selector: 'div.date-simple', text: true }
        ],
        'techcrunch.com': [
            { selector: 'time[datetime]', attribute: 'datetime' },
            { selector: '.post-block__meta time', text: true },
            { selector: '.meta__time', text: true }
        ],
        'arstechnica.com': [
            { selector: 'time[datetime]', attribute: 'datetime' },
            { selector: '.post-meta time', text: true },
            { selector: '.byline time', text: true }
        ],
        'politico.com': [
            { selector: 'time[datetime]', attribute: 'datetime' },
            { selector: '.timestamp', text: true },
            { selector: '.meta time', text: true }
        ],
        'bbc.com': [
            { selector: 'time[datetime]', attribute: 'datetime' },
            { selector: '[data-testid="card-metadata-lastupdated"]', text: true },
            { selector: '.mini-info-list__item time', text: true }
        ],
        'dw.com': [
            { selector: 'time[datetime]', attribute: 'datetime' },
            { selector: '.searchResult .date', text: true },
            { selector: '.article-details time', text: true }
        ]
    };
    
    const siteSpecificSelectors = dateSelectors[siteName] || [];
    const genericSelectors = [
        { selector: 'time[datetime]', attribute: 'datetime' },
        { selector: 'meta[property="article:published_time"]', attribute: 'content' },
        { selector: 'meta[name="pubdate"]', attribute: 'content' },
        { selector: 'meta[name="parsely-pub-date"]', attribute: 'content' },
        { selector: '.date', text: true },
        { selector: '.timestamp', text: true },
        { selector: 'time', text: true }
    ];

    const allSelectorsToTry = [...siteSpecificSelectors, ...genericSelectors];

    if (siteName === 'aljazeera.com') {
        console.log(`[AlJazeera DateDebug Cheerio] Trying to extract date for article. URL: ${articleUrl}`);
    }

    for (const selObj of allSelectorsToTry) {
        const dateElement = $container.find(selObj.selector).first();
        if (dateElement.length > 0) {
            let dateStr = selObj.attribute ? dateElement.attr(selObj.attribute) : (selObj.text ? dateElement.text().trim() : null);
            
            if (siteName === 'aljazeera.com') {
                console.log(`[AlJazeera DateDebug Cheerio] Selector: "${selObj.selector}", Found element: ${dateElement.length > 0}, Raw dateStr: "${dateStr}"`);
            }

            if (dateStr) {
                // Clean the date string
                let cleanedDateStr = dateStr.replace(/(Published\s*(on)?|Updated|Last update on|ET|\s*\|.*)/gi, '').trim();
                cleanedDateStr = cleanedDateStr.replace(/\b[A-Z]{3,5}\b(?!.*\d{4})/g, '').trim();
                cleanedDateStr = cleanedDateStr.replace(/(\d+)(st|nd|rd|th)/g, '$1');
                cleanedDateStr = cleanedDateStr.replace(/\bSept\b/i, 'Sep');

                if (siteName === 'aljazeera.com') {
                    console.log(`[AlJazeera DateDebug Cheerio] Cleaned dateStr: "${cleanedDateStr}"`);
                }

                // Try to parse the cleaned date
                const parsed = new Date(cleanedDateStr);
                if (!isNaN(parsed.getTime()) && parsed < now && parsed > new Date('2010-01-01')) {
                    if (siteName === 'aljazeera.com') {
                        console.log(`[AlJazeera DateDebug Cheerio] Successfully parsed date: ${parsed.toISOString()}`);
                    }
                    dateFound = true;
                    return parsed.toISOString();
                } else if (siteName === 'aljazeera.com') {
                    console.log(`[AlJazeera DateDebug Cheerio] Failed to parse date string "${cleanedDateStr}" into valid date. Parsed: ${parsed}`);
                }
                
                // Try relative date parsing
                const relativeMatch = cleanedDateStr.match(/(\d+)\s*(minute|min|hour|hr|day|week|month)s?\s*ago/i);
                if (relativeMatch) {
                    const amount = parseInt(relativeMatch[1]);
                    const unit = relativeMatch[2].toLowerCase();
                    let milliseconds = 0;
                    
                    switch (unit) {
                        case 'minute': case 'min': milliseconds = amount * 60 * 1000; break;
                        case 'hour': case 'hr': milliseconds = amount * 60 * 60 * 1000; break;
                        case 'day': milliseconds = amount * 24 * 60 * 60 * 1000; break;
                        case 'week': milliseconds = amount * 7 * 24 * 60 * 60 * 1000; break;
                        case 'month': milliseconds = amount * 30 * 24 * 60 * 60 * 1000; break;
                    }
                    
                    if (milliseconds > 0) {
                        const calculatedDate = new Date(now.getTime() - milliseconds);
                        if (siteName === 'aljazeera.com') {
                            console.log(`[AlJazeera DateDebug Cheerio] Parsed relative date: "${cleanedDateStr}" -> ${calculatedDate.toISOString()}`);
                        }
                        dateFound = true;
                        return calculatedDate.toISOString();
                    }
                }
            }
        }
    }
    
    if (siteName === 'aljazeera.com' && !dateFound) {
        console.warn(`[AlJazeera DateDebug Cheerio] ⚠️ No valid date found for Al Jazeera article. URL: ${articleUrl}. Using fallback. Container HTML snippet:`, $container.html()?.substring(0, 500));
    }
    return now.toISOString(); // Fallback
}
