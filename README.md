# Ghost Job Detector
https://docs.rs/tree-sitter/latest/tree_sitter/
A production-grade platform to help job seekers analyze job postings and identify potential "ghost jobs" - fake or inactive job listings that companies post without genuine hiring intent.

## Purpose

Job seekers spend countless hours applying to positions that may never be filled. Ghost jobs waste time, create false hope, and contribute to job search fatigue. This platform empowers job seekers by providing:

- **Transparency**: Analysis of job posting legitimacy based on multiple data points
- **Insights**: Clear breakdown of positive and warning signals
- **Community Intelligence**: Aggregated reports from other job seekers
- **Convenience**: Browser extension for real-time analysis while browsing LinkedIn

**Important**: We provide analysis and insights to help you make informed decisions - not definitive claims about whether a job is real or fake.

## Features

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
| **ATS Verification** | 25% | Job found on company's official ATS (Greenhouse, Lever, Workday) |
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

## Tech Stack

### Frontend (Next.js 16)
- **Framework**: Next.js 16 with App Router
- **Styling**: Tailwind CSS v4 with custom design tokens
- **Typography**: Inter (headings) + JetBrains Mono (monospace)
- **Components**: Custom components with shadcn/ui patterns

### Backend (FastAPI)
- **Framework**: FastAPI with async support
- **NLP Analysis**: Pattern-based text analysis (extensible to sentence-transformers)
- **ATS Verification**: Direct URL pattern matching for major ATS platforms
- **Storage**: In-memory (ready for Redis/Supabase integration)

### Chrome Extension
- **Manifest**: V3 (latest Chrome extension standard)
- **Content Scripts**: LinkedIn DOM reader
- **Popup**: Vanilla JS with modern CSS

### Infrastructure
- **Deployment**: Vercel with experimentalServices API
- **Architecture**: Microservices (frontend + backend as separate services)

## Project Structure

```
ghost-job-detector/
├── vercel.json              # Services configuration
├── frontend/                # Next.js web application
│   ├── app/
│   │   ├── layout.tsx       # Root layout with fonts
│   │   ├── page.tsx         # Main analyzer page
│   │   └── globals.css      # Tailwind + design tokens
│   ├── components/
│   │   ├── job-analyzer-form.tsx
│   │   ├── score-ring.tsx
│   │   ├── factor-breakdown.tsx
│   │   ├── insights-panel.tsx
│   │   └── community-reports.tsx
│   └── lib/
│       └── utils.ts
├── backend/                 # FastAPI Python backend
│   ├── main.py              # API routes + scoring engine
│   └── pyproject.toml       # Python dependencies
└── extension/               # Chrome extension
    ├── manifest.json
    ├── src/
    │   ├── content/         # LinkedIn content scripts
    │   ├── popup/           # Extension popup UI
    │   └── background/      # Service worker
    └── public/icons/
```

## API Reference

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

## Usage

### Web Application

1. Visit the deployed application URL
2. Paste a job description into the text area
3. (Optional) Add company name, job URL, posted date, and applicant count for deeper analysis
4. Click "Analyze Job Posting"
5. Review your legitimacy score and factor breakdown
6. Check community reports for additional insights
7. Submit your own report after applying

### Chrome Extension

1. Download the extension from `extension/` directory
2. Open Chrome and go to `chrome://extensions`
3. Enable "Developer mode" (top right)
4. Click "Load unpacked" and select the `extension/` folder
5. Navigate to any LinkedIn job posting
6. Click the extension icon to see the analysis
7. Or look for the score badge overlay on the job page

## Development

### Prerequisites
- Node.js 18+
- Python 3.11+
- pnpm (recommended) or npm

### Local Development

The project uses Vercel's experimentalServices API. When deployed or running via `vercel dev`, both services start automatically.

**Frontend only:**
```bash
cd frontend
pnpm install
pnpm dev
```

**Backend only:**
```bash
cd backend
pip install -e .
uvicorn main:app --reload
```

**Full stack (via Vercel):**
```bash
vercel dev
```

### Environment Variables

For production with full features, configure:

```env
# Supabase (for persistent storage)
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_anon_key

# Upstash Redis (for ATS caching)
UPSTASH_REDIS_REST_URL=your_redis_url
UPSTASH_REDIS_REST_TOKEN=your_redis_token
```

## Deployment

### Vercel (Recommended)

1. Push to GitHub
2. Import project in Vercel
3. Set Framework Preset to "Services" in Build Settings
4. Add environment variables
5. Deploy

### Chrome Web Store

1. Update `API_BASE_URL` in `extension/src/popup/popup.js` and `extension/src/content/content.js`
2. Run `cd extension && pnpm build` (or manually zip the extension folder)
3. Submit to Chrome Web Store Developer Dashboard

## Extending the Platform

### Adding New ATS Platforms

Edit `backend/main.py` and add patterns to `ATS_PATTERNS`:

```python
ATS_PATTERNS = {
    "greenhouse": {"domain": "greenhouse.io", "pattern": "/jobs/"},
    "lever": {"domain": "lever.co", "pattern": "/"},
    "workday": {"domain": "myworkdayjobs.com", "pattern": "/"},
    "your_ats": {"domain": "ats-domain.com", "pattern": "/careers/"},
}
```

### Adding Sentence Transformers (Advanced NLP)

For production-grade semantic analysis, add to `backend/main.py`:

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')

def calculate_semantic_similarity(desc1: str, desc2: str) -> float:
    embeddings = model.encode([desc1, desc2])
    return cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
```

### Connecting Real Database

Replace in-memory stores with Supabase/Redis:

```python
# Supabase example
from supabase import create_client
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_ANON_KEY"))

# Redis example
from upstash_redis import Redis
redis = Redis.from_env()
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Acknowledgments

Inspired by the need for transparency in job markets. Built to help job seekers make informed decisions and reduce time wasted on ghost job applications.
