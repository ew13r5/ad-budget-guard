import { useState, useEffect } from 'react'
import { StatusBadge } from '@/components/common/StatusBadge'
import { EmptyState } from '@/components/common/EmptyState'
import {
  Activity,
  AlertTriangle,
  Pause,
  Play,
  Shield,
  Bell,
  Filter,
  Inbox,
  ChevronDown,
  ChevronRight,
  Calendar,
} from 'lucide-react'

interface ActivityEvent {
  id: string
  time: string
  date: string
  type: 'anomaly' | 'pause' | 'resume' | 'alert' | 'rule_trigger'
  account: string
  campaign?: string
  message: string
  details?: {
    rule?: string
    threshold?: string
    actual?: string
    campaignsAffected?: string[]
  }
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
    details: {
      rule: 'Anomaly Detection',
      threshold: '3 sigma deviation',
      actual: '5.9x spend spike ($148.67/hr vs $25/hr normal)',
      campaignsAffected: ['Flash Sale Rush', 'Weekend Promo', 'Local Delivery Ads'],
    },
  },
  {
    id: '2',
    time: '14:23:05',
    date: 'Today',
    type: 'pause',
    account: 'Client-Delta',
    message: 'All campaigns hard paused by "Daily Budget Limit Guard" rule.',
    details: {
      rule: 'Daily Budget Limit Guard',
      threshold: '95% of daily budget',
      actual: '$892.00 / $150.00 (594.7%)',
      campaignsAffected: ['Flash Sale Rush', 'Weekend Promo', 'Local Delivery Ads', 'Brand Awareness', 'Competitor Targeting', 'Retargeting'],
    },
  },
  {
    id: '3',
    time: '14:22:30',
    date: 'Today',
    type: 'alert',
    account: 'Client-Gamma',
    campaign: 'Luxury Listings',
    message: 'Daily budget exceeded: $214.50 / $200.00 (107.3%). 3 campaigns auto-paused.',
    details: {
      rule: 'Daily Budget Limit Guard',
      threshold: '95% of $200.00 daily budget',
      actual: '$214.50 (107.3%)',
      campaignsAffected: ['Luxury Listings', 'Open House Weekend', 'Agent Recruitment'],
    },
  },
  {
    id: '4',
    time: '14:20:15',
    date: 'Today',
    type: 'rule_trigger',
    account: 'Client-Alpha',
    campaign: 'Summer Sale - Broad',
    message: 'Rule "Daily Budget Limit Guard" triggered: spend at 89.6% of budget.',
    details: {
      rule: 'Daily Budget Limit Guard',
      threshold: '95% of $200.00 daily budget',
      actual: '$174.20 (87.1%) — approaching threshold',
    },
  },
  {
    id: '5',
    time: '14:18:42',
    date: 'Today',
    type: 'anomaly',
    account: 'Client-Alpha',
    campaign: 'Product Catalog - DPA',
    message: 'Spend rate anomaly: 2.1x above average hourly rate.',
    details: {
      rule: 'Hourly Spend Rate Monitor',
      threshold: '2x daily average hourly rate',
      actual: '2.1x ($6.84/hr vs $3.26/hr average)',
      campaignsAffected: ['Product Catalog - DPA'],
    },
  },
  {
    id: '6',
    time: '14:15:00',
    date: 'Today',
    type: 'pause',
    account: 'Client-Alpha',
    campaign: 'Product Catalog - DPA',
    message: 'Campaign paused by "Hourly Spend Rate Monitor" rule.',
    details: {
      rule: 'Hourly Spend Rate Monitor',
      threshold: '2x daily average',
      actual: 'Budget reduced by 50%, campaign soft-paused',
      campaignsAffected: ['Product Catalog - DPA'],
    },
  },
  {
    id: '7',
    time: '13:45:20',
    date: 'Today',
    type: 'resume',
    account: 'Client-Beta',
    campaign: 'Trial Signup - Retarget',
    message: 'Campaign resumed manually after review.',
    details: {
      rule: 'Manual Override',
      actual: 'Spend rate normalized to 0.8x average',
    },
  },
  {
    id: '8',
    time: '12:30:00',
    date: 'Today',
    type: 'alert',
    account: 'Client-Alpha',
    message: 'Budget forecast: projected to reach 95% threshold by 16:00.',
    details: {
      rule: 'Daily Budget Limit Guard',
      threshold: '95% of $200.00 daily budget',
      actual: 'Current: $142.80 (71.4%), Hourly rate: $12.44/hr',
    },
  },
  {
    id: '9',
    time: '10:00:00',
    date: 'Today',
    type: 'rule_trigger',
    account: 'Client-Gamma',
    campaign: 'Open House Weekend',
    message: 'Rule "Monthly Budget Cap" evaluation: currently at 78% of monthly limit.',
    details: {
      rule: 'Monthly Budget Cap',
      threshold: '$5,000 monthly limit',
      actual: '$3,900.50 (78.0%)',
      campaignsAffected: ['Open House Weekend', 'Luxury Listings'],
    },
  },
  {
    id: '10',
    time: '09:15:00',
    date: 'Today',
    type: 'resume',
    account: 'Client-Gamma',
    campaign: 'Luxury Listings',
    message: 'Campaign budget reset for new day. All paused campaigns resumed.',
    details: {
      rule: 'Daily Reset',
      actual: 'New daily budget cycle started. 3 campaigns resumed.',
      campaignsAffected: ['Luxury Listings', 'Open House Weekend', 'Agent Recruitment'],
    },
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
const periodOptions = ['Today', 'Last 7 days', 'Last 30 days', 'All time'] as const

export default function ActivityPage() {
  useEffect(() => { document.title = 'Activity Log | Ad Budget Guard' }, [])
  const [filter, setFilter] = useState<string>('all')
  const [period, setPeriod] = useState<string>('Today')
  const [expandedId, setExpandedId] = useState<string | null>(null)

  const filtered = (() => {
    let events = filter === 'all' ? mockEvents : mockEvents.filter((e) => e.type === filter)
    // Cosmetic period filter — mock data is all "Today" so other periods show all
    if (period === 'Today') {
      events = events.filter((e) => e.date === 'Today')
    }
    return events
  })()

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
      <div className="flex flex-wrap items-center gap-2">
        {/* Period dropdown */}
        <div className="relative mr-2">
          <Calendar className="pointer-events-none absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-slate-500" />
          <select
            value={period}
            onChange={(e) => setPeriod(e.target.value)}
            className="appearance-none rounded-lg border border-[#2a2a3e] bg-[#0a0a0f] py-1.5 pl-8 pr-7 text-xs font-medium text-slate-300 transition-colors hover:border-[#3a3a4e] focus:border-blue-500 focus:outline-none"
          >
            {periodOptions.map((p) => (
              <option key={p} value={p}>{p}</option>
            ))}
          </select>
          <ChevronDown className="pointer-events-none absolute right-2 top-1/2 h-3 w-3 -translate-y-1/2 text-slate-500" />
        </div>

        <div className="h-5 w-px bg-[#2a2a3e]" />

        <Filter className="ml-1 h-4 w-4 text-slate-500" />
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
        {filtered.length === 0 && (
          <EmptyState
            icon={<Inbox className="h-10 w-10" />}
            title="No events found"
            description="No activity events match the selected filter."
          />
        )}
        {filtered.map((event) => {
          const config = typeConfig[event.type]
          const Icon = config.icon
          const isExpanded = expandedId === event.id

          return (
            <div
              key={event.id}
              className="rounded-xl border border-[#1a1a2e] bg-[#12121a] transition-colors hover:border-[#2a2a3e]"
            >
              <button
                type="button"
                onClick={() => setExpandedId(isExpanded ? null : event.id)}
                className="flex w-full items-start gap-4 p-4 text-left"
              >
                <div className="mt-0.5 rounded-lg bg-[#1a1a2e] p-2">
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
                <div className="mt-1 shrink-0 text-slate-500">
                  {isExpanded ? (
                    <ChevronDown className="h-4 w-4" />
                  ) : (
                    <ChevronRight className="h-4 w-4" />
                  )}
                </div>
              </button>

              {/* Expandable details */}
              <div
                className="overflow-hidden transition-all duration-200"
                style={{
                  maxHeight: isExpanded ? '200px' : '0px',
                  opacity: isExpanded ? 1 : 0,
                }}
              >
                {event.details && (
                  <div className="border-t border-[#1a1a2e] px-4 pb-4 pt-3 pl-16">
                    <div className="grid grid-cols-1 gap-2 text-xs sm:grid-cols-2">
                      {event.details.rule && (
                        <div>
                          <span className="font-medium text-slate-500">Rule: </span>
                          <span className="text-slate-300">{event.details.rule}</span>
                        </div>
                      )}
                      {event.details.threshold && (
                        <div>
                          <span className="font-medium text-slate-500">Threshold: </span>
                          <span className="text-slate-300">{event.details.threshold}</span>
                        </div>
                      )}
                      {event.details.actual && (
                        <div className="sm:col-span-2">
                          <span className="font-medium text-slate-500">Actual: </span>
                          <span className="text-slate-300">{event.details.actual}</span>
                        </div>
                      )}
                      {event.details.campaignsAffected && event.details.campaignsAffected.length > 0 && (
                        <div className="sm:col-span-2">
                          <span className="font-medium text-slate-500">Campaigns affected: </span>
                          <span className="text-slate-300">{event.details.campaignsAffected.join(', ')}</span>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
