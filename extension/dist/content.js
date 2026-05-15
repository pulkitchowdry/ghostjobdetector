/**
 * Ghost Job Detector - Content Script
 * Reads job data from LinkedIn job pages (does NOT scrape or make requests to LinkedIn)
 */

// API endpoint - change this to your deployed API URL
const API_BASE = 'http://localhost:8000';

/**
 * Extract job data from the currently displayed LinkedIn job page
 * This only reads the DOM elements that are already visible to the user
 */
function extractJobData() {
  const data = {
    job_title: '',
    company_name: '',
    job_description: '',
    posted_date: '',
    applicant_count: null,
    job_url: window.location.href,
    location: ''
  };
  
  // Job title - multiple possible selectors
  const titleSelectors = [
    '.job-details-jobs-unified-top-card__job-title',
    '.jobs-unified-top-card__job-title',
    'h1.t-24',
    '.job-title'
  ];
  
  for (const selector of titleSelectors) {
    const el = document.querySelector(selector);
    if (el && el.textContent) {
      data.job_title = el.textContent.trim();
      break;
    }
  }
  
  // Company name
  const companySelectors = [
    '.job-details-jobs-unified-top-card__company-name',
    '.jobs-unified-top-card__company-name',
    '.job-details-jobs-unified-top-card__primary-description-container a',
    '.company-name'
  ];
  
  for (const selector of companySelectors) {
    const el = document.querySelector(selector);
    if (el && el.textContent) {
      data.company_name = el.textContent.trim();
      break;
    }
  }
  
  // Job description
  const descSelectors = [
    '.jobs-description__content',
    '.jobs-description-content__text',
    '.job-details-jobs-unified-top-card__job-insight',
    '#job-details'
  ];
  
  for (const selector of descSelectors) {
    const el = document.querySelector(selector);
    if (el && el.textContent) {
      data.job_description = el.textContent.trim();
      break;
    }
  }
  
  // Posted date
  const dateSelectors = [
    '.jobs-unified-top-card__posted-date',
    '.job-details-jobs-unified-top-card__primary-description-container span:contains("ago")',
    'span.tvm__text--neutral'
  ];
  
  for (const selector of dateSelectors) {
    try {
      const el = document.querySelector(selector);
      if (el && el.textContent && el.textContent.includes('ago')) {
        data.posted_date = el.textContent.trim();
        break;
      }
    } catch {
      // Some selectors may fail, continue
    }
  }
  
  // Also try to find date in text content
  if (!data.posted_date) {
    const allSpans = document.querySelectorAll('span');
    for (const span of allSpans) {
      const text = span.textContent || '';
      if (text.match(/\d+\s*(day|week|month|hour)s?\s*ago/i)) {
        data.posted_date = text.trim();
        break;
      }
    }
  }
  
  // Applicant count
  const applicantSelectors = [
    '.jobs-unified-top-card__applicant-count',
    '.job-details-jobs-unified-top-card__applicant-count'
  ];
  
  for (const selector of applicantSelectors) {
    const el = document.querySelector(selector);
    if (el && el.textContent) {
      const match = el.textContent.match(/(\d+)/);
      if (match) {
        data.applicant_count = parseInt(match[1]);
        break;
      }
    }
  }
  
  // Also try to find applicant count in text
  if (!data.applicant_count) {
    const allElements = document.querySelectorAll('span, div');
    for (const el of allElements) {
      const text = el.textContent || '';
      const match = text.match(/(\d+)\s*applicant/i);
      if (match) {
        data.applicant_count = parseInt(match[1]);
        break;
      }
    }
  }
  
  // Location
  const locationSelectors = [
    '.jobs-unified-top-card__bullet',
    '.job-details-jobs-unified-top-card__primary-description-container .t-black--light',
    '.job-location'
  ];
  
  for (const selector of locationSelectors) {
    const el = document.querySelector(selector);
    if (el && el.textContent && !el.textContent.includes('ago') && !el.textContent.includes('applicant')) {
      data.location = el.textContent.trim();
      break;
    }
  }
  
  return data;
}

/**
 * Create and show the analysis badge on the page
 */
function showAnalysisBadge(score, verdict) {
  // Remove existing badge if present
  const existing = document.getElementById('ghost-job-detector-badge');
  if (existing) {
    existing.remove();
  }
  
  const badge = document.createElement('div');
  badge.id = 'ghost-job-detector-badge';
  badge.className = 'gjd-badge';
  
  let colorClass = 'gjd-badge--yellow';
  if (score >= 70) colorClass = 'gjd-badge--green';
  else if (score < 40) colorClass = 'gjd-badge--red';
  
  badge.innerHTML = `
    <div class="gjd-badge__content ${colorClass}">
      <div class="gjd-badge__score">${score}</div>
      <div class="gjd-badge__label">Legitimacy Score</div>
      <div class="gjd-badge__verdict">${formatVerdict(verdict)}</div>
    </div>
  `;
  
  // Find a good place to insert the badge
  const targetSelectors = [
    '.jobs-unified-top-card__content--two-pane',
    '.job-details-jobs-unified-top-card__container',
    '.jobs-details__main-content'
  ];
  
  let target = null;
  for (const selector of targetSelectors) {
    target = document.querySelector(selector);
    if (target) break;
  }
  
  if (target) {
    target.insertBefore(badge, target.firstChild);
  } else {
    // Fallback: append to body as fixed element
    badge.style.position = 'fixed';
    badge.style.top = '80px';
    badge.style.right = '20px';
    badge.style.zIndex = '9999';
    document.body.appendChild(badge);
  }
}

function formatVerdict(verdict) {
  const verdictMap = {
    'highly_legitimate': 'Highly Legitimate',
    'mostly_positive': 'Mostly Positive',
    'mixed_signals': 'Mixed Signals',
    'multiple_warnings': 'Multiple Warnings',
    'likely_ghost_job': 'Likely Ghost Job'
  };
  return verdictMap[verdict] || verdict;
}

/**
 * Analyze the current job page
 */
async function analyzeCurrentJob() {
  const jobData = extractJobData();
  
  if (!jobData.job_title || !jobData.company_name) {
    console.log('[GhostJobDetector] Could not extract job data from page');
    return null;
  }
  
  // Send to background script for API call
  return new Promise((resolve) => {
    chrome.runtime.sendMessage(
      { type: 'ANALYZE_JOB', data: jobData },
      (response) => {
        if (response && response.success) {
          showAnalysisBadge(response.data.legitimacy_score, response.data.verdict);
          resolve(response.data);
        } else {
          console.error('[GhostJobDetector] Analysis failed:', response?.error);
          resolve(null);
        }
      }
    );
  });
}

// Listen for messages from popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'GET_JOB_DATA') {
    const jobData = extractJobData();
    sendResponse({ success: true, data: jobData });
  } else if (message.type === 'ANALYZE_PAGE') {
    analyzeCurrentJob().then((result) => {
      sendResponse({ success: !!result, data: result });
    });
    return true; // Keep channel open for async response
  }
});

// Auto-analyze when page loads (optional - can be disabled)
// Uncomment the following to enable auto-analysis:
// if (document.readyState === 'complete') {
//   setTimeout(analyzeCurrentJob, 2000);
// } else {
//   window.addEventListener('load', () => setTimeout(analyzeCurrentJob, 2000));
// }

console.log('[GhostJobDetector] Content script loaded');
