interface SpeedSelectorProps {
  currentSpeed: number
  onSpeedChange: (speed: 1 | 2 | 5 | 10) => void
  disabled?: boolean
}

const speeds = [1, 2, 5, 10] as const

export function SpeedSelector({ currentSpeed, onSpeedChange, disabled }: SpeedSelectorProps) {
  return (
    <div className="flex items-center gap-1 rounded-lg bg-[#0a0a0f] p-1">
      {speeds.map((speed) => (
        <button
          key={speed}
          onClick={() => onSpeedChange(speed)}
          disabled={disabled}
          className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
            currentSpeed === speed
              ? 'bg-blue-600 text-white shadow-sm'
              : 'text-slate-400 hover:text-slate-200 disabled:opacity-50'
          }`}
        >
          {speed}x
        </button>
      ))}
    </div>
  )
}
