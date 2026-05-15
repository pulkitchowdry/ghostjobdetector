/**
 * Ghost Job Detector - Background Service Worker
 * Handles API communication and caching
 */

// API endpoint - change this to your deployed API URL
const API_BASE = 'http://localhost:8000';

// Simple in-memory cache for the session
const analysisCache = new Map();

/**
 * Analyze a job posting via the API
 */
async function analyzeJob(jobData) {
  // Create cache key from job data
  const cacheKey = `${jobData.job_title}|${jobData.company_name}`.toLowerCase();
  
  // Check cache first
  if (analysisCache.has(cacheKey)) {
    console.log('[GhostJobDetector] Returning cached result');
    return analysisCache.get(cacheKey);
  }
  
  try {
    const response = await fetch(`${API_BASE}/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        job_title: jobData.job_title,
        company_name: jobData.company_name,
        job_description: jobData.job_description || '',
        posted_date: jobData.posted_date || null,
        applicant_count: jobData.applicant_count || null,
        job_url: jobData.job_url || null,
        location: jobData.location || null,
      }),
    });
    
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }
    
    const result = await response.json();
    
    // Cache the result
    analysisCache.set(cacheKey, result);
    
    return result;
  } catch (error) {
    console.error('[GhostJobDetector] API error:', error);
    throw error;
  }
}

/**
 * Submit a community report
 */
async function submitReport(jobId, reportType, fingerprint) {
  try {
    const response = await fetch(`${API_BASE}/report`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        job_id: jobId,
        report_type: reportType,
        fingerprint: fingerprint,
      }),
    });
    
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('[GhostJobDetector] Report submission error:', error);
    throw error;
  }
}

// Listen for messages from content scripts and popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'ANALYZE_JOB') {
    analyzeJob(message.data)
      .then((result) => {
        sendResponse({ success: true, data: result });
      })
      .catch((error) => {
        sendResponse({ success: false, error: error.message });
      });
    return true; // Keep channel open for async response
  }
  
  if (message.type === 'SUBMIT_REPORT') {
    submitReport(message.jobId, message.reportType, message.fingerprint)
      .then((result) => {
        sendResponse({ success: true, data: result });
      })
      .catch((error) => {
        sendResponse({ success: false, error: error.message });
      });
    return true;
  }
  
  if (message.type === 'GET_CACHE_STATS') {
    sendResponse({
      success: true,
      data: {
        cacheSize: analysisCache.size,
      },
    });
  }
});

console.log('[GhostJobDetector] Background service worker loaded');
