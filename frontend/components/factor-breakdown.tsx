"use client"

import { cn } from "@/lib/utils"

interface Factor {
  name: string
  score: number
  weight: number
  details: string
  indicators: string[]
}

interface FactorBreakdownProps {
  factors: Factor[]
}

export function FactorBreakdown({ factors }: FactorBreakdownProps) {
  const getScoreColor = (score: number) => {
    if (score >= 70) return "bg-score-high"
    if (score >= 40) return "bg-score-medium"
    return "bg-score-low"
  }
  
  const getScoreTextColor = (score: number) => {
    if (score >= 70) return "text-score-high"
    if (score >= 40) return "text-score-medium"
    return "text-score-low"
  }
  
  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-foreground">Analysis Breakdown</h3>
      <div className="space-y-3">
        {factors.map((factor) => (
          <div key={factor.name} className="bg-card rounded-lg p-4 border border-border">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <span className="font-medium text-foreground">{factor.name}</span>
                <span className="text-xs text-muted-foreground px-2 py-0.5 bg-muted rounded">
                  {Math.round(factor.weight * 100)}% weight
                </span>
              </div>
              <span className={cn("font-bold tabular-nums", getScoreTextColor(factor.score))}>
                {factor.score}
              </span>
            </div>
            
            {/* Progress bar */}
            <div className="h-2 bg-muted rounded-full overflow-hidden mb-2">
              <div 
                className={cn("h-full rounded-full transition-all duration-500", getScoreColor(factor.score))}
                style={{ width: `${factor.score}%` }}
              />
            </div>
            
            <p className="text-sm text-muted-foreground">{factor.details}</p>
            
            {factor.indicators.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-1">
                {factor.indicators.slice(0, 3).map((indicator, i) => (
                  <span 
                    key={i}
                    className="text-xs px-2 py-1 bg-secondary rounded text-secondary-foreground"
                  >
                    {indicator}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
