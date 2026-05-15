/**
 * Ghost Job Detector - Popup Script
 */

const content = document.getElementById('content');

// Check if we're on a LinkedIn job page
async function checkCurrentTab() {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    if (!tab.url || !tab.url.includes('linkedin.com/jobs')) {
      showNotLinkedIn();
      return;
    }
    
    // We're on LinkedIn jobs - try to get job data
    showLoading();
    
    chrome.tabs.sendMessage(tab.id, { type: 'GET_JOB_DATA' }, (response) => {
      if (chrome.runtime.lastError) {
        showError('Could not connect to LinkedIn page. Try refreshing the page.');
        return;
      }
      
      if (response && response.success && response.data.job_title) {
        showJobData(response.data);
      } else {
        showNoJobFound();
      }
    });
  } catch (error) {
    showError('An error occurred. Please try again.');
  }
}

function showNotLinkedIn() {
  content.innerHTML = `
    <div class="not-linkedin">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z"/>
        <rect x="2" y="9" width="4" height="12"/>
        <circle cx="4" cy="4" r="2"/>
      </svg>
      <p>Navigate to a LinkedIn job posting to analyze it for ghost job indicators.</p>
      <a href="https://www.linkedin.com/jobs" target="_blank" class="btn btn-primary">
        Go to LinkedIn Jobs
      </a>
    </div>
  `;
}

function showLoading() {
  content.innerHTML = `
    <div class="status">
      <div class="loading">
        <div class="spinner"></div>
        <span>Reading job data...</span>
      </div>
    </div>
  `;
}

function showNoJobFound() {
  content.innerHTML = `
    <div class="status">
      <svg class="status-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"/>
        <path d="M12 8v4M12 16h.01"/>
      </svg>
      <p class="status-text">
        Could not find job details on this page. Make sure you're viewing a specific job posting.
      </p>
    </div>
  `;
}

function showError(message) {
  content.innerHTML = `
    <div class="error">${message}</div>
    <button class="btn btn-secondary" onclick="checkCurrentTab()">Try Again</button>
  `;
}

function showJobData(jobData) {
  content.innerHTML = `
    <div style="margin-bottom: 16px;">
      <h3 style="font-size: 14px; font-weight: 600; margin-bottom: 4px;">${escapeHtml(jobData.job_title)}</h3>
      <p style="font-size: 13px; color: #9ca3af;">${escapeHtml(jobData.company_name)}</p>
      ${jobData.posted_date ? `<p style="font-size: 12px; color: #6b7280; margin-top: 4px;">${escapeHtml(jobData.posted_date)}</p>` : ''}
    </div>
    <button class="btn btn-primary" id="analyzeBtn">
      Analyze This Job
    </button>
  `;
  
  document.getElementById('analyzeBtn').addEventListener('click', () => analyzeJob(jobData));
}

async function analyzeJob(jobData) {
  const btn = document.getElementById('analyzeBtn');
  btn.disabled = true;
  btn.innerHTML = '<span class="loading"><span class="spinner"></span> Analyzing...</span>';
  
  chrome.runtime.sendMessage(
    { type: 'ANALYZE_JOB', data: jobData },
    (response) => {
      if (response && response.success) {
        showResults(response.data, jobData);
      } else {
        showError(response?.error || 'Analysis failed. Please try again.');
      }
    }
  );
}

function showResults(result, jobData) {
  const colorClass = result.legitimacy_score >= 70 ? 'green' : result.legitimacy_score >= 40 ? 'yellow' : 'red';
  const circumference = 2 * Math.PI * 60;
  const offset = circumference - (result.legitimacy_score / 100) * circumference;
  
  const verdictText = {
    'highly_legitimate': 'Highly Legitimate',
    'mostly_positive': 'Mostly Positive',
    'mixed_signals': 'Mixed Signals',
    'multiple_warnings': 'Multiple Warnings',
    'likely_ghost_job': 'Likely Ghost Job'
  }[result.verdict] || result.verdict;
  
  let html = `
    <div class="score-display">
      <div class="score-ring">
        <svg width="140" height="140" viewBox="0 0 140 140">
          <circle class="bg" cx="70" cy="70" r="60"/>
          <circle class="progress ${colorClass}" cx="70" cy="70" r="60" 
            stroke-dasharray="${circumference}" 
            stroke-dashoffset="${offset}"/>
        </svg>
        <div class="score-value">
          <div class="score-number ${colorClass}">${result.legitimacy_score}</div>
          <div class="score-label">Legitimacy</div>
        </div>
      </div>
      <span class="verdict ${colorClass}">${verdictText}</span>
    </div>
    
    <div class="factors">
      <h4 style="font-size: 12px; color: #6b7280; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px;">Factor Breakdown</h4>
  `;
  
  for (const factor of result.factors) {
    const fColor = factor.score >= 70 ? 'green' : factor.score >= 40 ? 'yellow' : 'red';
    html += `
      <div class="factor">
        <span class="factor-name">${factor.name}</span>
        <span class="factor-score ${fColor}">${factor.score}</span>
      </div>
    `;
  }
  
  html += '</div>';
  
  // Insights
  if (result.insights.length > 0 || result.warnings.length > 0) {
    html += '<div class="insights">';
    
    for (const insight of result.insights) {
      html += `
        <div class="insight positive">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
            <polyline points="22 4 12 14.01 9 11.01"/>
          </svg>
          <span>${escapeHtml(insight)}</span>
        </div>
      `;
    }
    
    for (const warning of result.warnings) {
      html += `
        <div class="insight warning">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
            <line x1="12" y1="9" x2="12" y2="13"/>
            <line x1="12" y1="17" x2="12.01" y2="17"/>
          </svg>
          <span>${escapeHtml(warning)}</span>
        </div>
      `;
    }
    
    html += '</div>';
  }
  
  html += `
    <button class="btn btn-secondary" onclick="checkCurrentTab()" style="margin-top: 16px;">
      Analyze Another Job
    </button>
  `;
  
  content.innerHTML = html;
  
  // Also show badge on the page
  chrome.tabs.query({ active: true, currentWindow: true }, ([tab]) => {
    chrome.tabs.sendMessage(tab.id, { type: 'ANALYZE_PAGE' });
  });
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// Initialize
checkCurrentTab();
