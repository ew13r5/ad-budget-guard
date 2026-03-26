interface SpendProgressBarProps {
  percent: number
  className?: string
  showLabel?: boolean
}

export function SpendProgressBar({ percent, className = '', showLabel = true }: SpendProgressBarProps) {
  const colorClass =
    percent > 100
      ? 'bg-red-500 animate-pulse'
      : percent > 70
        ? 'bg-amber-500'
        : 'bg-emerald-500'

  const bgClass =
    percent > 100
      ? 'bg-red-500/10'
      : percent > 70
        ? 'bg-amber-500/10'
        : 'bg-emerald-500/10'

  return (
    <div className={className}>
      {showLabel && (
        <div className="mb-1 flex items-center justify-between text-xs">
          <span className="text-slate-400">Budget Usage</span>
          <span
            className={
              percent > 100
                ? 'font-semibold text-red-400'
                : percent > 70
                  ? 'font-semibold text-amber-400'
                  : 'text-emerald-400'
            }
          >
            {percent.toFixed(1)}%
          </span>
        </div>
      )}
      <div className={`h-2 w-full overflow-hidden rounded-full ${bgClass}`}>
        <div
          className={`h-full rounded-full transition-all duration-500 ${colorClass}`}
          style={{ width: `${Math.min(percent, 100)}%` }}
        />
      </div>
    </div>
  )
}
