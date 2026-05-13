"use client"

import { useState } from "react"
import { cn } from "@/lib/utils"
import { Search, Loader2 } from "lucide-react"

interface JobFormData {
  job_title: string
  company_name: string
  job_description: string
  posted_date: string
  applicant_count: string
  job_url: string
  location: string
}

interface JobAnalyzerFormProps {
  onAnalyze: (data: JobFormData) => void
  isLoading: boolean
}

export function JobAnalyzerForm({ onAnalyze, isLoading }: JobAnalyzerFormProps) {
  const [formData, setFormData] = useState<JobFormData>({
    job_title: "",
    company_name: "",
    job_description: "",
    posted_date: "",
    applicant_count: "",
    job_url: "",
    location: "",
  })
  
  const [showAdvanced, setShowAdvanced] = useState(false)
  
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.job_title || !formData.company_name || !formData.job_description) return
    onAnalyze(formData)
  }
  
  const handleChange = (field: keyof JobFormData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }
  
  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="grid md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-foreground mb-2">
            Job Title <span className="text-score-low">*</span>
          </label>
          <input
            type="text"
            value={formData.job_title}
            onChange={(e) => handleChange("job_title", e.target.value)}
            placeholder="e.g. Senior Software Engineer"
            className="w-full px-4 py-3 bg-card border border-border rounded-lg text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
            required
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-foreground mb-2">
            Company Name <span className="text-score-low">*</span>
          </label>
          <input
            type="text"
            value={formData.company_name}
            onChange={(e) => handleChange("company_name", e.target.value)}
            placeholder="e.g. Acme Corp"
            className="w-full px-4 py-3 bg-card border border-border rounded-lg text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
            required
          />
        </div>
      </div>
      
      <div>
        <label className="block text-sm font-medium text-foreground mb-2">
          Job Description <span className="text-score-low">*</span>
        </label>
        <textarea
          value={formData.job_description}
          onChange={(e) => handleChange("job_description", e.target.value)}
          placeholder="Paste the full job description here..."
          rows={8}
          className="w-full px-4 py-3 bg-card border border-border rounded-lg text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring resize-none"
          required
        />
        <p className="text-xs text-muted-foreground mt-1">
          Paste the complete job description for the most accurate analysis
        </p>
      </div>
      
      {/* Advanced options toggle */}
      <button
        type="button"
        onClick={() => setShowAdvanced(!showAdvanced)}
        className="text-sm text-accent hover:underline"
      >
        {showAdvanced ? "Hide" : "Show"} additional details (optional)
      </button>
      
      {showAdvanced && (
        <div className="grid md:grid-cols-2 gap-4 p-4 bg-secondary/50 rounded-lg">
          <div>
            <label className="block text-sm font-medium text-foreground mb-2">
              Posted Date
            </label>
            <input
              type="text"
              value={formData.posted_date}
              onChange={(e) => handleChange("posted_date", e.target.value)}
              placeholder="e.g. 2 weeks ago, 2024-01-15"
              className="w-full px-4 py-3 bg-card border border-border rounded-lg text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-foreground mb-2">
              Applicant Count
            </label>
            <input
              type="text"
              value={formData.applicant_count}
              onChange={(e) => handleChange("applicant_count", e.target.value)}
              placeholder="e.g. 150"
              className="w-full px-4 py-3 bg-card border border-border rounded-lg text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-foreground mb-2">
              Job URL
            </label>
            <input
              type="url"
              value={formData.job_url}
              onChange={(e) => handleChange("job_url", e.target.value)}
              placeholder="https://linkedin.com/jobs/..."
              className="w-full px-4 py-3 bg-card border border-border rounded-lg text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-foreground mb-2">
              Location
            </label>
            <input
              type="text"
              value={formData.location}
              onChange={(e) => handleChange("location", e.target.value)}
              placeholder="e.g. San Francisco, CA (Remote)"
              className="w-full px-4 py-3 bg-card border border-border rounded-lg text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
        </div>
      )}
      
      <button
        type="submit"
        disabled={isLoading || !formData.job_title || !formData.company_name || !formData.job_description}
        className={cn(
          "w-full flex items-center justify-center gap-2 px-6 py-4 rounded-lg font-semibold text-lg transition-all",
          "bg-primary text-primary-foreground hover:bg-primary/90",
          "disabled:opacity-50 disabled:cursor-not-allowed"
        )}
      >
        {isLoading ? (
          <>
            <Loader2 className="w-5 h-5 animate-spin" />
            Analyzing...
          </>
        ) : (
          <>
            <Search className="w-5 h-5" />
            Analyze Job Posting
          </>
        )}
      </button>
    </form>
  )
}
