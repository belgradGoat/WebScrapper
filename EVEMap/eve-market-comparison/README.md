# EVE Market Comparison Tool

## Overview
The EVE Market Comparison Tool is designed to help users compare market data from EVE Online, including both public and private structures that require authentication. This tool utilizes the EVE Swagger API to fetch and display market information, allowing users to make informed decisions based on real-time data.

## Features
- Compare market prices between two different structures.
- Access private market data through EVE Online's SSO authentication.
- User-friendly interface for easy navigation and data visualization.

## Project Structure
```
eve-market-comparison
├── src
│   ├── index.html          # Main HTML page for the market comparison tool
│   ├── css
│   │   └── market-comparison.css  # Styles for the market comparison tool
│   ├── js
│   │   ├── eve-auth.js     # Handles authentication with EVE Online SSO
│   │   ├── eve-market-api.js # Interacts with the EVE Swagger API
│   │   ├── market-comparison.js # Logic for comparing markets
│   │   └── market-ui.js     # Updates the user interface based on market data
│   └── config
│       └── api-config.js    # Configuration settings for the API
├── package.json             # npm configuration file
└── README.md                # Project documentation
```

## Setup Instructions
1. Clone the repository:
   ```
   git clone <repository-url>
   cd eve-market-comparison
   ```

2. Install dependencies:
   ```
   npm install
   ```

3. Configure the API settings in `src/config/api-config.js` with your EVE Online API credentials.

4. Open `src/index.html` in a web browser to start using the tool.

## Usage
- Upon opening the tool, users will be prompted to log in using their EVE Online account.
- After authentication, users can select the structures they wish to compare.
- The tool will display the market data side by side, highlighting any differences in prices.

## Contributing
Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.

## License
This project is licensed under the MIT License. See the LICENSE file for more details.