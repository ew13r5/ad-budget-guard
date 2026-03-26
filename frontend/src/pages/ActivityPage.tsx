import { useState } from 'react'
import { StatusBadge } from '@/components/common/StatusBadge'
import {
  Activity,
  AlertTriangle,
  Pause,
  Play,
  Shield,
  Bell,
  Filter,
} from 'lucide-react'

interface ActivityEvent {
  id: string
  time: string
  date: string
  type: 'anomaly' | 'pause' | 'resume' | 'alert' | 'rule_trigger'
  account: string
  campaign?: string
  message: string
}

const mockEvents: ActivityEvent[] = [
  {
    id: '1',
    time: '14:23:05',
    date: 'Today',
    type: 'anomaly',
    account: 'Client-Delta',
    campaign: 'Flash Sale Rush',
    message: 'Anomaly detected: spend rate 5.9x above normal. Budget exceeded $892/$150.',
  },
  {
    id: '2',
    time: '14:23:05',
    date: 'Today',
    type: 'pause',
    account: 'Client-Delta',
    message: 'All campaigns hard paused by "Daily Budget Limit Guard" rule.',
  },
  {
    id: '3',
    time: '14:22:30',
    date: 'Today',
    type: 'alert',
    account: 'Client-Gamma',
    campaign: 'Luxury Listings',
    message: 'Daily budget exceeded: $214.50 / $200.00 (107.3%). 3 campaigns auto-paused.',
  },
  {
    id: '4',
    time: '14:20:15',
    date: 'Today',
    type: 'rule_trigger',
    account: 'Client-Alpha',
    campaign: 'Summer Sale - Broad',
    message: 'Rule "Daily Budget Limit Guard" triggered: spend at 89.6% of budget.',
  },
  {
    id: '5',
    time: '14:18:42',
    date: 'Today',
    type: 'anomaly',
    account: 'Client-Alpha',
    campaign: 'Product Catalog - DPA',
    message: 'Spend rate anomaly: 2.1x above average hourly rate.',
  },
  {
    id: '6',
    time: '14:15:00',
    date: 'Today',
    type: 'pause',
    account: 'Client-Alpha',
    campaign: 'Product Catalog - DPA',
    message: 'Campaign paused by "Hourly Spend Rate Monitor" rule.',
  },
  {
    id: '7',
    time: '13:45:20',
    date: 'Today',
    type: 'resume',
    account: 'Client-Beta',
    campaign: 'Trial Signup - Retarget',
    message: 'Campaign resumed manually after review.',
  },
  {
    id: '8',
    time: '12:30:00',
    date: 'Today',
    type: 'alert',
    account: 'Client-Alpha',
    message: 'Budget forecast: projected to reach 95% threshold by 16:00.',
  },
  {
    id: '9',
    time: '10:00:00',
    date: 'Today',
    type: 'rule_trigger',
    account: 'Client-Gamma',
    campaign: 'Open House Weekend',
    message: 'Rule "Monthly Budget Cap" evaluation: currently at 78% of monthly limit.',
  },
  {
    id: '10',
    time: '09:15:00',
    date: 'Today',
    type: 'resume',
    account: 'Client-Gamma',
    campaign: 'Luxury Listings',
    message: 'Campaign budget reset for new day. All paused campaigns resumed.',
  },
]

const typeConfig = {
  anomaly: { icon: AlertTriangle, variant: 'danger', label: 'Anomaly', color: 'text-red-400' },
  pause: { icon: Pause, variant: 'warning', label: 'Pause', color: 'text-amber-400' },
  resume: { icon: Play, variant: 'success', label: 'Resume', color: 'text-emerald-400' },
  alert: { icon: Bell, variant: 'warning', label: 'Alert', color: 'text-amber-400' },
  rule_trigger: { icon: Shield, variant: 'info', label: 'Rule', color: 'text-blue-400' },
}

const filterOptions = ['all', 'anomaly', 'pause', 'resume', 'alert', 'rule_trigger'] as const

export default function ActivityPage() {
  const [filter, setFilter] = useState<string>('all')

  const filtered = filter === 'all' ? mockEvents : mockEvents.filter((e) => e.type === filter)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="rounded-lg bg-blue-500/10 p-2">
            <Activity className="h-5 w-5 text-blue-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-100">Activity Log</h1>
            <p className="text-sm text-slate-500">
              Real-time feed of all budget guard actions and alerts
            </p>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-2">
        <Filter className="h-4 w-4 text-slate-500" />
        {filterOptions.map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
              filter === f
                ? 'bg-blue-600/10 text-blue-400'
                : 'text-slate-400 hover:bg-[#1a1a2e] hover:text-slate-200'
            }`}
          >
            {f === 'all' ? 'All' : f === 'rule_trigger' ? 'Rules' : f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
        <span className="ml-auto text-xs text-slate-500">{filtered.length} events</span>
      </div>

      {/* Event list */}
      <div className="space-y-2">
        {filtered.map((event) => {
          const config = typeConfig[event.type]
          const Icon = config.icon

          return (
            <div
              key={event.id}
              className="rounded-xl border border-[#1a1a2e] bg-[#12121a] p-4 transition-colors hover:border-[#2a2a3e]"
            >
              <div className="flex items-start gap-4">
                <div className={`mt-0.5 rounded-lg bg-[#1a1a2e] p-2`}>
                  <Icon className={`h-4 w-4 ${config.color}`} />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <StatusBadge variant={config.variant} label={config.label} />
                    <span className="text-xs font-medium text-slate-300">{event.account}</span>
                    {event.campaign && (
                      <>
                        <span className="text-xs text-slate-600">/</span>
                        <span className="text-xs text-slate-400">{event.campaign}</span>
                      </>
                    )}
                    <span className="ml-auto font-mono text-xs text-slate-500">
                      {event.date} {event.time}
                    </span>
                  </div>
                  <p className="mt-1.5 text-sm text-slate-300">{event.message}</p>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
