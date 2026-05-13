"use client"

import { useState } from "react"
import { JobAnalyzerForm } from "@/components/job-analyzer-form"
import { ScoreRing } from "@/components/score-ring"
import { FactorBreakdown } from "@/components/factor-breakdown"
import { InsightsPanel } from "@/components/insights-panel"
import { CommunityReports } from "@/components/community-reports"
import { Shield, Chrome, Github, ArrowRight, RefreshCw } from "lucide-react"

interface AnalysisResult {
  legitimacy_score: number
  verdict: string
  job_id: string
  factors: Array<{
    name: string
    score: number
    weight: number
    details: string
    indicators: string[]
  }>
  insights: string[]
  warnings: string[]
  ats_verified: boolean | null
  ats_url: string | null
  community_stats: {
    total_reports: number
    interview_scheduled: number
    response_received: number
    no_response: number
    offer_received: number
  }
}

export default function HomePage() {
  const API_URL = process.env.NEXT_PUBLIC_API_URL
  const [result, setResult] = useState<AnalysisResult | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  const handleAnalyze = async (data: {
    job_title: string
    company_name: string
    job_description: string
    posted_date: string
    applicant_count: string
    job_url: string
    location: string
  }) => {
    setIsLoading(true)
    setError(null)
    
    try {
      const response = await fetch(`${API_URL}/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          job_title: data.job_title,
          company_name: data.company_name,
          job_description: data.job_description,
          posted_date: data.posted_date || null,
          applicant_count: data.applicant_count ? parseInt(data.applicant_count) : null,
          job_url: data.job_url || null,
          location: data.location || null,
        }),
      })
      
      if (!response.ok) {
        throw new Error("Analysis failed. Please try again.")
      }
      
      const analysisResult = await response.json()
      setResult(analysisResult)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong")
    } finally {
      setIsLoading(false)
    }
  }
  
  const handleReset = () => {
    setResult(null)
    setError(null)
  }
  
  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="border-b border-border">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Shield className="w-8 h-8 text-primary" />
            <span className="text-xl font-bold text-foreground">GhostJobDetector</span>
          </div>
          <nav className="flex items-center gap-4">
            <a 
              href="#extension" 
              className="text-sm text-muted-foreground hover:text-foreground transition-colors flex items-center gap-1"
            >
              <Chrome className="w-4 h-4" />
              Extension
            </a>
            <a 
              href="https://github.com" 
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-muted-foreground hover:text-foreground transition-colors flex items-center gap-1"
            >
              <Github className="w-4 h-4" />
              GitHub
            </a>
          </nav>
        </div>
      </header>
      
      <main className="max-w-6xl mx-auto px-4 py-12">
        {!result ? (
          <>
            {/* Hero Section */}
            <div className="text-center mb-12">
              <h1 className="text-4xl md:text-5xl font-bold text-foreground mb-4 text-balance">
                Is That Job Posting Real?
              </h1>
              <p className="text-lg text-muted-foreground max-w-2xl mx-auto text-pretty">
                Analyze job postings for legitimacy indicators. We check ATS verification, 
                description quality, posting freshness, and community reports to help you 
                make informed decisions.
              </p>
            </div>
            
            {/* Analyzer Form */}
            <div className="max-w-3xl mx-auto">
              <div className="bg-card border border-border rounded-xl p-6 md:p-8">
                <JobAnalyzerForm onAnalyze={handleAnalyze} isLoading={isLoading} />
                
                {error && (
                  <div className="mt-4 p-4 bg-destructive/10 border border-destructive/30 rounded-lg text-destructive text-sm">
                    {error}
                  </div>
                )}
              </div>
            </div>
            
            {/* Features Section */}
            <div className="mt-20 grid md:grid-cols-3 gap-6">
              <div className="bg-card border border-border rounded-xl p-6">
                <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                  <Shield className="w-6 h-6 text-primary" />
                </div>
                <h3 className="text-lg font-semibold text-foreground mb-2">ATS Verification</h3>
                <p className="text-muted-foreground text-sm">
                  We check if the job exists on the company&apos;s official careers page through 
                  Greenhouse, Lever, Workday, and other ATS systems.
                </p>
              </div>
              
              <div className="bg-card border border-border rounded-xl p-6">
                <div className="w-12 h-12 bg-accent/10 rounded-lg flex items-center justify-center mb-4">
                  <svg className="w-6 h-6 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold text-foreground mb-2">Description Analysis</h3>
                <p className="text-muted-foreground text-sm">
                  Our NLP engine analyzes job descriptions for specificity, red flags, 
                  and generic language that may indicate a ghost job.
                </p>
              </div>
              
              <div className="bg-card border border-border rounded-xl p-6">
                <div className="w-12 h-12 bg-score-high/10 rounded-lg flex items-center justify-center mb-4">
                  <svg className="w-6 h-6 text-score-high" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold text-foreground mb-2">Community Reports</h3>
                <p className="text-muted-foreground text-sm">
                  See what other job seekers experienced - whether they got interviews, 
                  responses, or no reply at all.
                </p>
              </div>
            </div>
            
            {/* Chrome Extension CTA */}
            <div id="extension" className="mt-20 bg-card border border-border rounded-xl p-8 md:p-12">
              <div className="flex flex-col md:flex-row items-center gap-8">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-4">
                    <Chrome className="w-8 h-8 text-foreground" />
                    <span className="text-sm font-medium text-primary px-2 py-1 bg-primary/10 rounded">
                      Coming Soon
                    </span>
                  </div>
                  <h2 className="text-2xl md:text-3xl font-bold text-foreground mb-4">
                    Chrome Extension
                  </h2>
                  <p className="text-muted-foreground mb-6">
                    Analyze LinkedIn job postings with one click. Our extension reads the 
                    job details from the page you&apos;re viewing and shows you the legitimacy 
                    score instantly.
                  </p>
                  <button 
                    disabled
                    className="flex items-center gap-2 px-6 py-3 bg-secondary text-secondary-foreground rounded-lg font-medium opacity-50 cursor-not-allowed"
                  >
                    <Chrome className="w-5 h-5" />
                    Get Chrome Extension
                    <ArrowRight className="w-4 h-4" />
                  </button>
                </div>
                <div className="flex-shrink-0">
                  <div className="w-64 h-48 bg-secondary rounded-lg flex items-center justify-center">
                    <div className="text-center">
                      <Chrome className="w-16 h-16 text-muted-foreground mx-auto mb-2" />
                      <p className="text-sm text-muted-foreground">Extension Preview</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </>
        ) : (
          /* Results View */
          <div>
            <button
              onClick={handleReset}
              className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors mb-8"
            >
              <RefreshCw className="w-4 h-4" />
              Analyze another job
            </button>
            
            <div className="grid lg:grid-cols-3 gap-8">
              {/* Score Column */}
              <div className="lg:col-span-1">
                <div className="bg-card border border-border rounded-xl p-6 text-center sticky top-8">
                  <h2 className="text-lg font-semibold text-foreground mb-6">Legitimacy Score</h2>
                  <ScoreRing score={result.legitimacy_score} />
                  
                  <div className="mt-6 pt-6 border-t border-border">
                    <InsightsPanel 
                      insights={result.insights}
                      warnings={result.warnings}
                      atsVerified={result.ats_verified}
                      atsUrl={result.ats_url}
                    />
                  </div>
                </div>
              </div>
              
              {/* Details Column */}
              <div className="lg:col-span-2 space-y-6">
                <FactorBreakdown factors={result.factors} />
                
                <CommunityReports 
                  jobId={result.job_id}
                  stats={result.community_stats}
                />
                
                {/* Disclaimer */}
                <div className="bg-secondary/50 rounded-lg p-4 text-sm text-muted-foreground">
                  <strong className="text-foreground">Disclaimer:</strong> This analysis is based on 
                  available data and heuristics. It provides insights to help you make informed 
                  decisions but cannot definitively determine if a job is real or fake.
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
      
      {/* Footer */}
      <footer className="border-t border-border mt-20">
        <div className="max-w-6xl mx-auto px-4 py-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <Shield className="w-5 h-5 text-primary" />
              <span className="font-semibold text-foreground">GhostJobDetector</span>
            </div>
            <p className="text-sm text-muted-foreground">
              Helping job seekers make informed decisions
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}
