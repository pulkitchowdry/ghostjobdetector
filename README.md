# Ghost Job Detector

## Overview

A production-grade platform to help job seekers analyze job postings and identify potential "ghost jobs" - fake or inactive job listings that companies post without genuine hiring intent.

## Problem

Job seekers spend countless hours applying to positions that may never be filled. Ghost jobs waste time, create false hope, and contribute to job search fatigue. This platform empowers job seekers by providing:

- **Transparency**: Analysis of job posting legitimacy based on multiple data points
- **Insights**: Clear breakdown of positive and warning signals
- **Community Intelligence**: Aggregated reports from other job seekers
- **Convenience**: Browser extension for real-time analysis while browsing LinkedIn

**Important**: We provide analysis and insights to help you make informed decisions - not definitive claims about whether a job is real or fake.

## Outcome

### Features

### Web Application
- Paste any job description for instant analysis
- Legitimacy score (0-100) with visual breakdown
- Six-factor analysis with individual scoring
- Community reports showing interview rates and response rates
- Optional fields for deeper analysis (company name, job URL, posted date)

### Chrome Extension
- Analyzes LinkedIn job pages in real-time
- Displays legitimacy score badge on job listings
- Quick popup view with full analysis
- Submit community reports directly from LinkedIn

### Scoring Factors

| Factor | Weight | What Increases Score |
|--------|--------|----------------------|
| **ATS Verification** | 25% | Job found on company's official ATS (Greenhouse, Lever, Workday, Smartrecruiters) |
| **Description Quality** | 20% | Specific requirements, clear responsibilities, real tech stack |
| **Posting Freshness** | 15% | Recently posted (within 2 weeks ideal) |
| **Applicant Ratio** | 10% | Reasonable applicant count for posting age |
| **Uniqueness** | 15% | Not repeatedly reposted, unique description |
| **Community Signals** | 15% | Reports of interviews scheduled, HR responses received |

### Score Interpretation
- **80-100**: Strong legitimacy indicators - apply with confidence
- **60-79**: Mostly positive signals - worth applying
- **40-59**: Mixed signals - proceed with caution, research company
- **20-39**: Multiple warning signs - verify directly with company
- **0-19**: High likelihood of ghost job - consider skipping

## Demo

### Product Screenshots
### Home page
<img width="1074" height="772" alt="image" src="https://github.com/user-attachments/assets/382f3dfd-d984-4975-8666-5f5fdb024876" />

Job seekers can enter details related to the job. It is mandatory to provide the below details,
1. Job title
2. Company name
3. Job description

Following are some optional details that can be added and will help in providing a more accurate score,
1. Job posting date
2. Number of applicants
3. LinkedIn URL
4. Location

Note - While using the Chrome extension (which works on the linkedin jobs page), the above details will be fetched automatically.

### Analysis
<img width="1093" height="774" alt="image" src="https://github.com/user-attachments/assets/37bad269-9f38-4175-a1c5-da2f7890c138" />

System provides an overall score for the respective job along with a proper breakdown of different categories. It also provides a brief statement which shares the reasoning for the respective category score. 

Community signals is a feature which allows users to participate and help other job seekers in identifying fake jobs.

## Tech Stack

### Frontend (Next.js 16)
- **Framework**: Next.js 16 with App Router
- **Styling**: Tailwind CSS v4 with custom design tokens
- **Typography**: Inter (headings) + JetBrains Mono (monospace)
- **Components**: Custom components with shadcn/ui patterns

### Backend (FastAPI)
- **Framework**: FastAPI with async support
- **NLP Analysis**: Pattern-based text analysis (extensible to sentence-transformers)
- **ATS Verification**: Direct URL pattern matching for major ATS platforms (Currently support Greenhouse and Smartrecruiters with Workday and Lever coming soon!)
- **Storage**: Supabase database

### Chrome Extension
- **Manifest**: V3 (latest Chrome extension standard)
- **Content Scripts**: LinkedIn DOM reader
- **Popup**: Vanilla JS with modern CSS

### Infrastructure
- **Deployment**: Vercel for frontend and AWS Lambda for backend
- **Architecture**: Microservices (frontend + backend as separate services)

### API Reference

### Analyze Job
```http
POST /api/analyze
Content-Type: application/json

{
  "description": "Full job description text...",
  "company_name": "Company Inc",        // optional
  "job_url": "https://...",             // optional
  "posted_date": "2026-05-01",          // optional
  "applicant_count": 150                // optional
}
```

**Response:**
```json
{
  "legitimacy_score": 73,
  "verdict": "mostly_positive",
  "analysis": {
    "ats_verified": true,
    "ats_details": "Job found on company Greenhouse careers page",
    "description_quality": 68,
    "description_notes": ["Specific tech stack mentioned", "Clear team structure"],
    "freshness_score": 85,
    "days_posted": 5,
    "applicant_ratio_score": 60,
    "uniqueness_score": 70,
    "community_score": 75,
    "community_reports": {
      "interview_scheduled": 3,
      "response_received": 5,
      "no_response": 2
    }
  },
  "insights": [
    "Job verified on company ATS - good sign",
    "Posted recently with reasonable applicant count"
  ]
}
```

### Submit Community Report
```http
POST /api/report
Content-Type: application/json

{
  "job_hash": "abc123...",
  "report_type": "interview_scheduled",  // or "response_received", "no_response", "offer_received"
  "company_name": "Company Inc",
  "job_title": "Software Engineer"
}
```

### Get Community Reports
```http
GET /api/reports/{job_hash}
```

### Health Check
```http
GET /api/health
```

## Installation

### Prerequisites
- Node.js 18+
- Python 3.11+
- pnpm (recommended) or npm

**Frontend only:**
```bash
cd frontend
pnpm install
pnpm dev
```

**Backend only:**
```bash
cd backend
source .venv/bin/activate - In order to have a virtual environment where the packages can be installed
pip install -e .
uvicorn main:app --reload
```

**Full stack (via Vercel):**
```bash
vercel dev
```
Access localhost:3000 on the browser with the API service running on localhost:8000 for local development

### How to run Chrome Extension in dev mode

1. Download the extension from `extension/` directory
2. Open Chrome and go to `chrome://extensions`
3. Enable "Developer mode" (top right)
4. Click "Load unpacked" and select the `extension/` folder
5. Navigate to any LinkedIn job posting
6. Click the extension icon to see the analysis
7. Or look for the score badge overlay on the job page

## Deployment

### Vercel (Recommended for frontend)

1. Push to GitHub
2. Import project in Vercel
3. Add environment variables
4. Deploy

### AWS (Recommended for backend)

1. Install AWS CLI and login using 'aws login'
2. Install serverless framework and login - npm i -g serverless
3. Install Docker (This is because certain libraries in AWS Lambda might not work)
4. Add environment variables in AWS Lambda
5. Run serverless deploy
6. Copy the AWS endpoint and add it to your Frontend environement variables


### Chrome Web Store

1. Update `API_BASE_URL` in `extension/src/popup/popup.js` and `extension/src/content/content.js`
2. Run `cd extension && pnpm build` (or manually zip the extension folder)
3. Submit to Chrome Web Store Developer Dashboard

## How to use
There are two ways to use this application,
1. Webpage
2. Chrome extension - On LinkedIn pages for now

### Webpage
Enter information about the job like job title, company name, job description and few optional details like date posted, number of applications, etc. 
Click on Analyze and wait for the results

Every analysis gets an overall score with proper breakdown across different categories displayed on the right.
Participate in the community submission if you have applied to the job and help everyone identify real jobs.

### Chrome Extension
Currently the extension works only on LinkedIn jobs page.
Click on the extensions icon in the top right corner on Chrome after opening a job on LinkedIn
Click on Analyze and observe the results on the widget
Access the webpage for detailed results

## Project Structure

```
ghostjobdetector/
├── backend                          # FastAPI based backend
│   ├── core                         # Core services - Logging, Search, Constants
│   │   ├── __init__.py
│   │   ├── constants
│   │   │   ├── __init__.py
│   │   │   └── ats_patterns.py
│   │   ├── db.py
│   │   ├── logging.py
│   │   └── search
│   │       ├── __init__.py
│   │       └── careers_finder.py
│   ├── data_services                # Database services - Supabase
│   │   ├── __init__.py
│   │   ├── ats_details.py
│   │   ├── companies.py
│   │   └── jobs.py
│   ├── info.txt
│   ├── main.py
│   ├── package-lock.json
│   ├── package.json
│   ├── pyproject.toml                # Project information with list of dependecies
│   ├── requirements.txt
│   ├── services                        # List of Services directory
│   │   ├── applicant_ratio            # Applicant ratio analysis
│   │   │   ├── __init__.py
│   │   │   └── applicant_ratio.py
│   │   ├── ats                        # ATS system related to files
│   │   │   ├── __init__.py
│   │   │   ├── ats_info.json
│   │   │   ├── base.py
│   │   │   ├── greenhouse_sample_list.txt
│   │   │   ├── greenhouse.py
│   │   │   ├── registry.py
│   │   │   ├── smartrecruiter_sample_job.txt
│   │   │   ├── smartrecruiter_sample_list.txt
│   │   │   ├── smartrecruiters.py
│   │   │   └── verifier.py
│   │   ├── community                    # Community submissions
│   │   │   ├── __init__.py
│   │   │   └── community_submission.py
│   │   ├── description                    # Job description analysis
│   │   │   ├── __init__.py
│   │   │   ├── description_analyzer.py
│   │   │   └── description_dictionary.py
│   │   ├── job_recency                    # Job freshness analysis
│   │   │   ├── __init__.py
│   │   │   └── job_freshness.py
│   │   └── job_uniqueness                # Duplicate job identifier
│   │       ├── __init__.py
│   │       └── job_unique.py
│   └── utils
│   |   ├── __init__.py
│   |   └── matchscoring.py
|   |__ serverless.yml                    # Serverless Framework file to deploy on AWS
├── components                        
│   ├── theme-provider.tsx
│   └── ui              
│       ├── accordion.tsx
│       ├── alert-dialog.tsx
│       ├── alert.tsx
│       ├── aspect-ratio.tsx
│       ├── avatar.tsx
│       ├── badge.tsx
├── extension                    # Chrome extension
│   ├── build.js
│   ├── manifest.json
│   ├── package.json
│   ├── public
│   │   └── icons
│   │       ├── icon128.png
│   │       ├── icon16.png
│   │       ├── icon32.png
│   │       └── icon48.png
│   ├── README.md
│   └── src
│       ├── background
│       │   └── background.js
│       ├── content
│       │   ├── content.css
│       │   └── content.js
│       └── popup
│           ├── popup.html
│           └── popup.js
├── frontend                            # Next.js based frontend
│   ├── app
|   |   ├── api                         # Handling API route to backend
|   |   |   └──[...slug]
|   |   |       └──route.ts
│   │   ├── globals.css
│   │   ├── layout.tsx
│   │   └── page.tsx
│   ├── components                        # Frontend UI components
│   │   ├── community-reports.tsx
│   │   ├── factor-breakdown.tsx
│   │   ├── insights-panel.tsx
│   │   ├── job-analyzer-form.tsx
│   │   └── score-ring.tsx
│   ├── lib
│   │   └── utils.ts
│   ├── next-env.d.ts
│   ├── next.config.ts
│   ├── package-lock.json
│   ├── package.json
│   ├── pnpm-lock.yaml
│   ├── pnpm-workspace.yaml
│   ├── postcss.config.mjs
│   └── tsconfig.json
├── docs                           
│   ├── ai-dev
|   |   ├── README.md               # Details on how AI was used in the development of this project
├── README.md
```

## Reflection
Through this project, I was able to identify a structure in flagging ghost jobs on various online platforms and could also observe how ATS systems work. The next steps are to improve the analysis and help people identify right job opportunities.

## Final note
Inspired by the need for transparency in job markets. Built to help job seekers make informed decisions and reduce time wasted on ghost job applications.
