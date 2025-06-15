# WebScraper Project

## Overview
WebScraper is a news aggregation application that fetches articles from various sources and provides users with a dashboard to view and summarize the latest news. The application includes a feature to generate a brief summary of the fetched articles using the Google Gemini API.

## Project Structure
```
WebScraper
├── public
│   ├── news_dashboard.html      # HTML structure for the news dashboard
│   ├── css
│   │   └── styles.css           # Styles for the news dashboard
│   └── js
│       └── script.js            # JavaScript code for handling user interactions
├── src
│   └── server.js                # Express server setup and API handling
├── package.json                  # npm configuration file
└── README.md                     # Project documentation
```

## Features
- Fetches news articles from multiple sources.
- Displays articles in a user-friendly dashboard.
- Provides a "Provide Brief" button to generate a summary of the news articles.
- Utilizes the Google Gemini API for summarization.

## Setup Instructions
1. **Clone the repository:**
   ```
   git clone <repository-url>
   cd WebScraper
   ```

2. **Install dependencies:**
   ```
   npm install
   ```

3. **Run the server:**
   ```
   node src/server.js
   ```

4. **Open the application:**
   Navigate to `http://localhost:3000` in your web browser to access the news dashboard.

## Usage
- Click the "Provide Brief" button to generate a summary of the latest news articles.
- The summary will be displayed in the designated area on the dashboard.

## Dependencies
- Express: Web framework for Node.js.
- CORS: Middleware for enabling Cross-Origin Resource Sharing.
- Node-fetch: For making HTTP requests to external APIs.
- Cheerio: For parsing HTML from static sites.
- Puppeteer: For scraping dynamic sites that use JavaScript.

## Future Enhancements
- Implement user authentication for personalized news feeds.
- Add support for additional languages in the summarization feature.
- Enhance the UI with more interactive elements and better styling.

## License
This project is licensed under the MIT License. See the LICENSE file for more details.