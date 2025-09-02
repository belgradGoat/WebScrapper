#!/usr/bin/env node

/**
 * Eagle Watchtower MCP Server
 * Provides LLM access to news aggregation, social media monitoring, and AI summarization
 * Compatible with MCP SDK v1.17.4
 */

const { McpServer } = require('@modelcontextprotocol/sdk/server/mcp.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const { z } = require('zod');
const fetch = require('node-fetch');

// Configuration
const EAGLE_API_URL = process.env.EAGLE_API_URL || 'http://localhost:3000';

// Initialize MCP Server
const mcpServer = new McpServer({
  name: 'eagle-watchtower',
  version: '1.0.0',
  description: 'MCP server for Eagle Watchtower news aggregation and analysis'
});

// Register tool: search_news
mcpServer.registerTool('search_news', {
  description: 'Search news across multiple sources (GNews, web scraping, Google News RSS, Guardian API)',
  inputSchema: {
    query: z.string().describe('Search query/keyword'),
    max_results: z.number().optional().default(20).describe('Maximum number of results (default: 20)'),
    language: z.string().optional().default('en').describe('Language code (e.g., "en", "pl")'),
    country: z.string().optional().default('us').describe('Country code (e.g., "us", "uk")')
  }
}, async ({ query, max_results = 20, language = 'en', country = 'us' }) => {
  try {
    console.error(`[MCP] Searching news for: ${query}`);
    
    const params = new URLSearchParams({
      q: query,
      max: max_results,
      lang: language,
      country: country
    });
    
    const response = await fetch(`${EAGLE_API_URL}/api/news?${params}`);
    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.error || 'News search failed');
    }
    
    const formattedResponse = {
      total: data.totalArticles,
      sources_used: data.sources,
      search_term: data.searchTerm,
      articles: data.articles?.map(article => ({
        title: article.title,
        description: article.description,
        url: article.url,
        source: article.source?.name,
        published: article.publishedAt,
        image: article.urlToImage
      })) || []
    };
    
    return {
      content: [{
        type: 'text',
        text: JSON.stringify(formattedResponse, null, 2)
      }]
    };
  } catch (error) {
    console.error('[MCP] News search error:', error);
    return {
      content: [{
        type: 'text',
        text: `Error searching news: ${error.message}\n\nMake sure Eagle Watchtower is running on ${EAGLE_API_URL}`
      }]
    };
  }
});

// Register tool: search_bluesky
mcpServer.registerTool('search_bluesky', {
  description: 'Search Bluesky social media posts',
  inputSchema: {
    query: z.string().describe('Search query'),
    limit: z.number().optional().default(50).describe('Maximum posts to return (max: 100)')
  }
}, async ({ query, limit = 50 }) => {
  try {
    console.error(`[MCP] Searching Bluesky for: ${query}`);
    
    const response = await fetch(`${EAGLE_API_URL}/api/bluesky`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, limit })
    });
    
    const data = await response.json();
    
    if (!response.ok || !data.success) {
      throw new Error(data.error || 'Bluesky search failed');
    }
    
    const formattedPosts = {
      total: data.totalPosts,
      query: query,
      posts: data.posts?.map(post => ({
        author: post.author.handle,
        text: post.text,
        url: post.url,
        likes: post.engagement.likes,
        reposts: post.engagement.reposts,
        replies: post.engagement.replies,
        timestamp: post.timestamp
      })) || []
    };
    
    return {
      content: [{
        type: 'text',
        text: JSON.stringify(formattedPosts, null, 2)
      }]
    };
  } catch (error) {
    console.error('[MCP] Bluesky search error:', error);
    return {
      content: [{
        type: 'text',
        text: `Error searching Bluesky: ${error.message}`
      }]
    };
  }
});

// Register tool: search_reddit
mcpServer.registerTool('search_reddit', {
  description: 'Search Reddit posts and discussions',
  inputSchema: {
    query: z.string().describe('Search query'),
    limit: z.number().optional().default(50).describe('Maximum posts to return (max: 100)')
  }
}, async ({ query, limit = 50 }) => {
  try {
    console.error(`[MCP] Searching Reddit for: ${query}`);
    
    const response = await fetch(`${EAGLE_API_URL}/api/reddit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, limit })
    });
    
    const data = await response.json();
    
    if (!response.ok || !data.success) {
      throw new Error(data.error || 'Reddit search failed');
    }
    
    const formattedPosts = {
      total: data.totalPosts,
      query: query,
      posts: data.posts?.map(post => ({
        title: post.title,
        text: post.text,
        subreddit: post.subreddit,
        author: post.author.username,
        url: post.url,
        score: post.engagement.score,
        comments: post.engagement.comments,
        upvote_ratio: post.engagement.upvotes,
        timestamp: post.timestamp
      })) || []
    };
    
    return {
      content: [{
        type: 'text',
        text: JSON.stringify(formattedPosts, null, 2)
      }]
    };
  } catch (error) {
    console.error('[MCP] Reddit search error:', error);
    return {
      content: [{
        type: 'text',
        text: `Error searching Reddit: ${error.message}`
      }]
    };
  }
});

// Register tool: search_all_sources
mcpServer.registerTool('search_all_sources', {
  description: 'Search across all available sources (news, Reddit, Bluesky) simultaneously',
  inputSchema: {
    query: z.string().describe('Search query'),
    max_results_per_source: z.number().optional().default(20).describe('Max results from each source')
  }
}, async ({ query, max_results_per_source = 20 }) => {
  try {
    console.error(`[MCP] Searching all sources for: ${query}`);
    
    // Parallel search across all sources
    const [newsRes, blueskyRes, redditRes] = await Promise.allSettled([
      fetch(`${EAGLE_API_URL}/api/news?${new URLSearchParams({ q: query, max: max_results_per_source })}`),
      fetch(`${EAGLE_API_URL}/api/bluesky`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, limit: max_results_per_source })
      }),
      fetch(`${EAGLE_API_URL}/api/reddit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, limit: max_results_per_source })
      })
    ]);
    
    const results = {
      query: query,
      news: null,
      bluesky: null,
      reddit: null
    };
    
    // Process news results
    if (newsRes.status === 'fulfilled') {
      const newsData = await newsRes.value.json();
      if (newsRes.value.ok) {
        results.news = {
          total: newsData.totalArticles,
          sources: newsData.sources,
          articles: newsData.articles?.slice(0, 10).map(a => ({
            title: a.title,
            source: a.source?.name,
            url: a.url
          })) || []
        };
      }
    }
    
    // Process Bluesky results
    if (blueskyRes.status === 'fulfilled') {
      const blueskyData = await blueskyRes.value.json();
      if (blueskyRes.value.ok && blueskyData.success) {
        results.bluesky = {
          total: blueskyData.totalPosts,
          posts: blueskyData.posts?.slice(0, 5).map(p => ({
            author: p.author.handle,
            text: p.text.substring(0, 200) + (p.text.length > 200 ? '...' : ''),
            engagement: p.engagement.likes + p.engagement.reposts
          })) || []
        };
      }
    }
    
    // Process Reddit results
    if (redditRes.status === 'fulfilled') {
      const redditData = await redditRes.value.json();
      if (redditRes.value.ok && redditData.success) {
        results.reddit = {
          total: redditData.totalPosts,
          posts: redditData.posts?.slice(0, 5).map(p => ({
            title: p.title,
            subreddit: p.subreddit,
            score: p.engagement.score
          })) || []
        };
      }
    }
    
    return {
      content: [{
        type: 'text',
        text: JSON.stringify(results, null, 2)
      }]
    };
  } catch (error) {
    console.error('[MCP] All sources search error:', error);
    return {
      content: [{
        type: 'text',
        text: `Error searching all sources: ${error.message}`
      }]
    };
  }
});

// Register tool: generate_ai_summary
mcpServer.registerTool('generate_ai_summary', {
  description: 'Generate AI-powered summary using Gemma AI with weighted source analysis (70% news, 30% social)',
  inputSchema: {
    query: z.string().describe('Topic to analyze and summarize'),
    custom_prompt: z.string().optional().describe('Optional custom prompt for the AI'),
    include_social: z.boolean().optional().default(true).describe('Include social media sources in summary')
  }
}, async ({ query, custom_prompt, include_social = true }) => {
  try {
    console.error(`[MCP] Generating AI summary for: ${query}`);
    
    // First, gather articles from news sources
    const newsRes = await fetch(`${EAGLE_API_URL}/api/news?${new URLSearchParams({ q: query, max: 50 })}`);
    const newsData = await newsRes.json();
    let articles = newsData.articles || [];
    
    // Optionally include social media
    if (include_social) {
      try {
        // Add Bluesky posts
        const blueskyRes = await fetch(`${EAGLE_API_URL}/api/bluesky`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query, limit: 20 })
        });
        const blueskyData = await blueskyRes.json();
        
        if (blueskyData.success && blueskyData.posts) {
          blueskyData.posts.forEach(post => {
            articles.push({
              title: `Bluesky: ${post.text.substring(0, 100)}`,
              description: post.text,
              source: { name: 'Bluesky', type: 'social' }
            });
          });
        }
        
        // Add Reddit posts
        const redditRes = await fetch(`${EAGLE_API_URL}/api/reddit`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query, limit: 20 })
        });
        const redditData = await redditRes.json();
        
        if (redditData.success && redditData.posts) {
          redditData.posts.forEach(post => {
            articles.push({
              title: post.title,
              description: post.text || post.title,
              source: { name: 'Reddit', type: 'social' }
            });
          });
        }
      } catch (socialError) {
        console.error('[MCP] Social media fetch error:', socialError);
      }
    }
    
    if (articles.length === 0) {
      return {
        content: [{
          type: 'text',
          text: 'No articles available for summarization.'
        }]
      };
    }
    
    // Generate summary using Gemma
    const summaryRes = await fetch(`${EAGLE_API_URL}/api/summarize-gemma`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        articles: articles,
        prompt: custom_prompt || `Create a comprehensive analysis of "${query}" based on the provided sources. Focus primarily on news sources and use social media as supporting context.`
      })
    });
    
    const summaryData = await summaryRes.json();
    
    if (!summaryRes.ok || summaryData.error) {
      throw new Error(summaryData.error || 'Summary generation failed');
    }
    
    return {
      content: [{
        type: 'text',
        text: summaryData.summary || 'Summary generation completed but no text was returned.'
      }]
    };
  } catch (error) {
    console.error('[MCP] AI summary error:', error);
    return {
      content: [{
        type: 'text',
        text: `Error generating AI summary: ${error.message}`
      }]
    };
  }
});

// Register tool: get_weather
mcpServer.registerTool('get_weather', {
  description: 'Get weather information from US National Weather Service',
  inputSchema: {
    latitude: z.number().optional().describe('Latitude (optional, uses default location if not provided)'),
    longitude: z.number().optional().describe('Longitude (optional, uses default location if not provided)')
  }
}, async ({ latitude, longitude }) => {
  try {
    console.error('[MCP] Getting weather data');
    
    const requestBody = {};
    if (latitude && longitude) {
      requestBody.lat = latitude;
      requestBody.lon = longitude;
    }
    
    const response = await fetch(`${EAGLE_API_URL}/api/weather`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestBody)
    });
    
    const data = await response.json();
    
    if (!response.ok || !data.success) {
      throw new Error(data.error || 'Weather fetch failed');
    }
    
    const weatherInfo = {
      location: `${data.location.city}, ${data.location.state}`,
      coordinates: { lat: data.location.lat, lon: data.location.lon },
      current: data.current ? {
        temperature: `${data.current.temperature_f}°F`,
        conditions: data.current.conditions,
        wind: data.current.wind
      } : null,
      forecast: data.forecast?.slice(0, 3).map(period => ({
        period: period.name,
        temperature: `${period.temperature}°${period.temperature_unit}`,
        conditions: period.short_forecast,
        rain_chance: period.precipitation_chance
      })) || [],
      alerts: data.alerts || []
    };
    
    return {
      content: [{
        type: 'text',
        text: JSON.stringify(weatherInfo, null, 2)
      }]
    };
  } catch (error) {
    console.error('[MCP] Weather error:', error);
    return {
      content: [{
        type: 'text',
        text: `Error getting weather: ${error.message}`
      }]
    };
  }
});

// Register tool: get_summary_history
mcpServer.registerTool('get_summary_history', {
  description: 'Retrieve historical AI summaries from MongoDB',
  inputSchema: {
    limit: z.number().optional().default(10).describe('Number of recent summaries to retrieve')
  }
}, async ({ limit = 10 }) => {
  try {
    console.error('[MCP] Getting summary history');
    
    const response = await fetch(`${EAGLE_API_URL}/api/summaries`);
    const data = await response.json();
    
    if (!response.ok || !data.success) {
      throw new Error(data.error || 'Failed to retrieve summaries');
    }
    
    const summaries = {
      source: data.source,
      count: data.summaries?.length || 0,
      summaries: data.summaries?.slice(0, limit).map(s => ({
        id: s._id,
        timestamp: s.timestamp,
        search_term: s.search_term,
        preview: s.summary?.substring(0, 200) + '...',
        sources: {
          news: s.source_breakdown?.news_sources,
          social: s.source_breakdown?.social_sources,
          total: s.source_breakdown?.total_articles
        }
      })) || []
    };
    
    return {
      content: [{
        type: 'text',
        text: JSON.stringify(summaries, null, 2)
      }]
    };
  } catch (error) {
    console.error('[MCP] Summary history error:', error);
    return {
      content: [{
        type: 'text',
        text: `Error getting summary history: ${error.message}`
      }]
    };
  }
});

// Start the MCP server
async function main() {
  console.error('[MCP] Starting Eagle Watchtower MCP Server...');
  console.error(`[MCP] Connecting to Eagle Watchtower at: ${EAGLE_API_URL}`);
  
  const transport = new StdioServerTransport();
  await mcpServer.connect(transport);
  
  console.error('[MCP] Eagle Watchtower MCP Server is running');
  console.error('[MCP] Available tools:');
  console.error('  - search_news: Multi-source news search');
  console.error('  - search_bluesky: Bluesky social media search');
  console.error('  - search_reddit: Reddit posts search');
  console.error('  - search_all_sources: Combined search across all sources');
  console.error('  - generate_ai_summary: AI-powered analysis with Gemma');
  console.error('  - get_weather: Weather information');
  console.error('  - get_summary_history: Historical summaries from MongoDB');
}

main().catch((error) => {
  console.error('[MCP] Fatal error:', error);
  process.exit(1);
});