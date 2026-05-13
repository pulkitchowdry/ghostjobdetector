"use client"

interface ScoreRingProps {
  score: number
  size?: number
  strokeWidth?: number
}

export function ScoreRing({ score, size = 180, strokeWidth = 12 }: ScoreRingProps) {
  const radius = (size - strokeWidth) / 2
  const circumference = radius * 2 * Math.PI
  const offset = circumference - (score / 100) * circumference
  
  const getScoreColor = () => {
    if (score >= 70) return "var(--color-score-high)"
    if (score >= 40) return "var(--color-score-medium)"
    return "var(--color-score-low)"
  }
  
  const getScoreLabel = () => {
    if (score >= 80) return "Highly Legitimate"
    if (score >= 60) return "Mostly Positive"
    if (score >= 40) return "Mixed Signals"
    if (score >= 20) return "Multiple Warnings"
    return "Likely Ghost Job"
  }
  
  const getGlowClass = () => {
    if (score >= 70) return "glow-green"
    if (score >= 40) return "glow-yellow"
    return "glow-red"
  }
  
  return (
    <div className={`relative inline-flex items-center justify-center rounded-full ${getGlowClass()}`}>
      <svg width={size} height={size} className="transform -rotate-90">
        {/* Background circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="var(--color-muted)"
          strokeWidth={strokeWidth}
        />
        {/* Score circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={getScoreColor()}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="score-ring transition-all duration-1000 ease-out"
          style={{ strokeDashoffset: offset }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span 
          className="text-5xl font-bold tabular-nums"
          style={{ color: getScoreColor() }}
        >
          {score}
        </span>
        <span className="text-sm text-muted-foreground mt-1">
          {getScoreLabel()}
        </span>
      </div>
    </div>
  )
}
