# Ghost Job Detector - Chrome Extension

A Chrome extension that helps you analyze LinkedIn job postings for legitimacy indicators.

## Features

- **One-Click Analysis**: Click the extension while viewing any LinkedIn job posting
- **Legitimacy Score**: Get a 0-100 score indicating how likely the job is to be real
- **Factor Breakdown**: See detailed analysis of ATS verification, description quality, and more
- **Community Reports**: See what other job seekers experienced with this posting

## Installation (Development)

1. Build the extension:
   ```bash
   cd extension
   npm run build
   ```

2. Open Chrome and go to `chrome://extensions/`

3. Enable "Developer mode" in the top right

4. Click "Load unpacked" and select the `extension/dist` folder

5. The extension icon should appear in your toolbar

## Usage

1. Navigate to any LinkedIn job posting (e.g., `https://www.linkedin.com/jobs/view/...`)

2. Click the Ghost Job Detector extension icon

3. Click "Analyze This Job" to get the legitimacy analysis

4. Review the score, factor breakdown, and insights

## Configuration

Before using, update the `API_BASE` constant in these files to point to your deployed API:

- `src/content/content.js`
- `src/background/background.js`

## How It Works

The extension reads the job information from the LinkedIn page DOM (it does NOT scrape LinkedIn or make requests to LinkedIn servers). It simply extracts the visible text content and sends it to our analysis API.

### Privacy

- We only read data from the page you're actively viewing
- No LinkedIn credentials are accessed
- No background data collection
- Analysis data is used only for providing the service
