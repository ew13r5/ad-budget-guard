import { useRef, useEffect } from 'react'
import { StatusBadge } from '@/components/common/StatusBadge'
import { AlertTriangle, Pause, Play, Zap, Clock, Bell, DollarSign, ShieldAlert } from 'lucide-react'

interface LogEntry {
  id: string
  time: string
  type: string
  message: string
  campaignId?: string
}

interface SimulationLogProps {
  entries: LogEntry[]
}

const typeIcons: Record<string, typeof AlertTriangle> = {
  anomaly: AlertTriangle,
  pause: Pause,
  resume: Play,
  trigger: Zap,
  tick: Clock,
  alert: Bell,
  spend: DollarSign,
  warning: ShieldAlert,
}

const typeVariants: Record<string, string> = {
  anomaly: 'danger',
  pause: 'warning',
  resume: 'success',
  trigger: 'danger',
  tick: 'info',
  alert: 'warning',
  spend: 'info',
  warning: 'danger',
}

export function SimulationLog({ entries }: SimulationLogProps) {
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight
    }
  }, [entries.length])

  if (entries.length === 0) {
    return (
      <div className="flex items-center justify-center py-8 text-sm text-slate-500">
        No events recorded yet
      </div>
    )
  }

  return (
    <div ref={containerRef} className="max-h-64 space-y-1 overflow-y-auto">
      {entries.map((entry) => {
        const Icon = typeIcons[entry.type] || Clock
        const variant = typeVariants[entry.type] || 'info'

        return (
          <div
            key={entry.id}
            className="flex items-start gap-3 rounded-lg px-3 py-2 transition-colors hover:bg-[#1a1a2e]/50"
          >
            <Icon className="mt-0.5 h-3.5 w-3.5 shrink-0 text-slate-500" />
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs text-slate-500">{entry.time}</span>
                <StatusBadge variant={variant} label={entry.type} />
              </div>
              <p className="mt-0.5 text-xs text-slate-300">{entry.message}</p>
              {entry.campaignId && (
                <span className="mt-0.5 inline-block text-xs text-slate-500">
                  Campaign: {entry.campaignId}
                </span>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}
