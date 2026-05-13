"use client"

import { cn } from "@/lib/utils"
import { CheckCircle2, AlertTriangle, Info } from "lucide-react"

interface InsightsPanelProps {
  insights: string[]
  warnings: string[]
  atsVerified?: boolean | null
  atsUrl?: string | null
}

export function InsightsPanel({ insights, warnings, atsVerified, atsUrl }: InsightsPanelProps) {
  return (
    <div className="space-y-4">
      {/* ATS Status */}
      <div className={cn(
        "rounded-lg p-4 border",
        atsVerified === true ? "bg-score-high/10 border-score-high/30" :
        atsVerified === false ? "bg-score-low/10 border-score-low/30" :
        "bg-muted/50 border-border"
      )}>
        <div className="flex items-start gap-3">
          {atsVerified === true ? (
            <CheckCircle2 className="w-5 h-5 text-score-high mt-0.5" />
          ) : atsVerified === false ? (
            <AlertTriangle className="w-5 h-5 text-score-low mt-0.5" />
          ) : (
            <Info className="w-5 h-5 text-muted-foreground mt-0.5" />
          )}
          <div>
            <p className={cn(
              "font-medium",
              atsVerified === true ? "text-score-high" :
              atsVerified === false ? "text-score-low" :
              "text-muted-foreground"
            )}>
              {atsVerified === true ? "ATS Verified" :
               atsVerified === false ? "Not Found on ATS" :
               "ATS Check Unavailable"}
            </p>
            <p className="text-sm text-muted-foreground mt-1">
              {atsVerified === true ? "This job was found on the company's official careers page." :
               atsVerified === false ? "We couldn't find this job on the company's careers page." :
               "We don't have ATS data for this company yet."}
            </p>
            {atsUrl && (
              <a 
                href={atsUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-accent hover:underline mt-2 inline-block"
              >
                View company careers page
              </a>
            )}
          </div>
        </div>
      </div>
      
      {/* Positive Insights */}
      {insights.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-muted-foreground uppercase tracking-wider">
            Positive Signals
          </h4>
          <div className="space-y-2">
            {insights.map((insight, i) => (
              <div key={i} className="flex items-start gap-2 text-sm">
                <CheckCircle2 className="w-4 h-4 text-score-high mt-0.5 shrink-0" />
                <span className="text-foreground">{insight}</span>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* Warnings */}
      {warnings.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-muted-foreground uppercase tracking-wider">
            Warning Signs
          </h4>
          <div className="space-y-2">
            {warnings.map((warning, i) => (
              <div key={i} className="flex items-start gap-2 text-sm">
                <AlertTriangle className="w-4 h-4 text-score-low mt-0.5 shrink-0" />
                <span className="text-foreground">{warning}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
