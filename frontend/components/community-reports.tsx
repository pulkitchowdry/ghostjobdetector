"use client"

import { useState } from "react"
import { cn } from "@/lib/utils"
import { MessageSquare, ThumbsUp, ThumbsDown, Calendar, Mail } from "lucide-react"

interface CommunityStats {
  total_reports: number
  interview_scheduled: number
  response_received: number
  no_response: number
  offer_received: number
}

interface CommunityReportsProps {
  jobId: string
  stats: CommunityStats
  onReport?: (type: string) => void
}

export function CommunityReports({ jobId, stats, onReport }: CommunityReportsProps) {
  const API_URL = process.env.NEXT_PUBLIC_API_URL
  const [submitted, setSubmitted] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  
  const handleReport = async (type: string) => {
    if (isSubmitting || submitted) return
    
    setIsSubmitting(true)
    try {
      const response = await fetch(`${API_URL}/report`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          job_id: jobId,
          report_type: type,
          fingerprint: typeof window !== "undefined" ? btoa(navigator.userAgent).slice(0, 32) : null,
        }),
      })
      
      if (response.ok) {
        setSubmitted(type)
        onReport?.(type)
      }
    } catch (error) {
      console.error("Failed to submit report:", error)
    } finally {
      setIsSubmitting(false)
    }
  }
  
  const reportTypes = [
    { type: "interview_scheduled", label: "Got Interview", icon: Calendar, color: "text-score-high" },
    { type: "response_received", label: "Got Response", icon: Mail, color: "text-accent" },
    { type: "no_response", label: "No Response", icon: ThumbsDown, color: "text-score-low" },
    { type: "offer_received", label: "Got Offer", icon: ThumbsUp, color: "text-score-high" },
  ]
  
  const total = stats.total_reports
  const positive = stats.interview_scheduled + stats.response_received + stats.offer_received
  const positivePercent = total > 0 ? Math.round((positive / total) * 100) : 0
  
  return (
    <div className="bg-card rounded-lg p-4 border border-border">
      <div className="flex items-center gap-2 mb-4">
        <MessageSquare className="w-5 h-5 text-muted-foreground" />
        <h3 className="font-semibold text-foreground">Community Reports</h3>
        {total > 0 && (
          <span className="text-xs px-2 py-0.5 bg-muted rounded text-muted-foreground">
            {total} reports
          </span>
        )}
      </div>
      
      {total > 0 ? (
        <div className="mb-4">
          <div className="flex justify-between text-sm mb-1">
            <span className="text-muted-foreground">Response Rate</span>
            <span className={cn(
              "font-medium",
              positivePercent >= 50 ? "text-score-high" : "text-score-low"
            )}>
              {positivePercent}% positive
            </span>
          </div>
          <div className="h-2 bg-muted rounded-full overflow-hidden">
            <div 
              className="h-full bg-score-high rounded-full transition-all"
              style={{ width: `${positivePercent}%` }}
            />
          </div>
          
          <div className="grid grid-cols-4 gap-2 mt-3 text-center">
            <div>
              <span className="text-lg font-bold text-score-high">{stats.interview_scheduled}</span>
              <p className="text-xs text-muted-foreground">Interviews</p>
            </div>
            <div>
              <span className="text-lg font-bold text-accent">{stats.response_received}</span>
              <p className="text-xs text-muted-foreground">Responses</p>
            </div>
            <div>
              <span className="text-lg font-bold text-score-low">{stats.no_response}</span>
              <p className="text-xs text-muted-foreground">No Reply</p>
            </div>
            <div>
              <span className="text-lg font-bold text-score-high">{stats.offer_received}</span>
              <p className="text-xs text-muted-foreground">Offers</p>
            </div>
          </div>
        </div>
      ) : (
        <p className="text-sm text-muted-foreground mb-4">
          No community reports yet. Be the first to share your experience!
        </p>
      )}
      
      {/* Report buttons */}
      <div className="border-t border-border pt-4">
        <p className="text-sm text-muted-foreground mb-3">
          {submitted ? "Thanks for your feedback!" : "Share your experience with this job:"}
        </p>
        <div className="grid grid-cols-2 gap-2">
          {reportTypes.map(({ type, label, icon: Icon, color }) => (
            <button
              key={type}
              onClick={() => handleReport(type)}
              disabled={isSubmitting || !!submitted}
              className={cn(
                "flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all",
                submitted === type 
                  ? "bg-primary text-primary-foreground" 
                  : submitted
                  ? "bg-muted text-muted-foreground cursor-not-allowed"
                  : "bg-secondary text-secondary-foreground hover:bg-secondary/80"
              )}
            >
              <Icon className={cn("w-4 h-4", submitted ? "" : color)} />
              {label}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
