import { useState, useEffect } from 'react'
import { StatusBadge } from '@/components/common/StatusBadge'
import {
  ShieldCheck,
  Plus,
  Edit3,
  Trash2,
  DollarSign,
  Calendar,
  Clock,
  Zap,
} from 'lucide-react'

interface Rule {
  id: string
  name: string
  type: string
  typeLabel: string
  condition: string
  action: string
  actionType: string
  isActive: boolean
  icon: typeof DollarSign
  color: string
  bgColor: string
}

const mockRules: Rule[] = [
  {
    id: 'r1',
    name: 'Daily Budget Limit Guard',
    type: 'daily_limit',
    typeLabel: 'Daily',
    condition: 'When daily spend exceeds 95% of budget',
    action: 'Pause campaign and send alert',
    actionType: 'Soft Pause',
    isActive: true,
    icon: DollarSign,
    color: 'text-emerald-400',
    bgColor: 'bg-emerald-500/10',
  },
  {
    id: 'r2',
    name: 'Monthly Budget Cap',
    type: 'monthly_limit',
    typeLabel: 'Monthly',
    condition: 'When monthly spend exceeds $5,000 per account',
    action: 'Pause all campaigns in account',
    actionType: 'Hard Pause',
    isActive: true,
    icon: Calendar,
    color: 'text-blue-400',
    bgColor: 'bg-blue-500/10',
  },
  {
    id: 'r3',
    name: 'Hourly Spend Rate Monitor',
    type: 'hourly_rate',
    typeLabel: 'Hourly',
    condition: 'When hourly spend rate exceeds 2x the daily average',
    action: 'Reduce budget by 50% and alert',
    actionType: 'Soft Pause',
    isActive: true,
    icon: Clock,
    color: 'text-purple-400',
    bgColor: 'bg-purple-500/10',
  },
  {
    id: 'r4',
    name: 'Anomaly Detection',
    type: 'anomaly',
    typeLabel: 'Anomaly',
    condition: 'When spend pattern deviates 3 sigma from historical norm',
    action: 'Hard pause campaign, require manual review',
    actionType: 'Hard Pause',
    isActive: false,
    icon: Zap,
    color: 'text-amber-400',
    bgColor: 'bg-amber-500/10',
  },
]

export default function RulesPage() {
  useEffect(() => { document.title = 'Budget Rules | Ad Budget Guard' }, [])
  const [rules, setRules] = useState(mockRules)

  function toggleRule(id: string) {
    setRules((prev) =>
      prev.map((r) => (r.id === id ? { ...r, isActive: !r.isActive } : r))
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="rounded-lg bg-purple-500/10 p-2">
            <ShieldCheck className="h-5 w-5 text-purple-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-100">Budget Rules</h1>
            <p className="text-sm text-slate-500">
              Configure automated budget protection rules
            </p>
          </div>
        </div>
        <button className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-blue-700">
          <Plus className="h-4 w-4" />
          Add Rule
        </button>
      </div>

      {/* Rules list */}
      <div className="space-y-3">
        {rules.map((rule) => (
          <div
            key={rule.id}
            className={`rounded-xl border p-5 transition-all ${
              rule.isActive
                ? 'border-[#1a1a2e] bg-[#12121a]'
                : 'border-[#1a1a2e]/50 bg-[#12121a]/50 opacity-60'
            }`}
          >
            <div className="flex items-start justify-between">
              <div className="flex items-start gap-4">
                <div className={`rounded-lg p-2.5 ${rule.bgColor}`}>
                  <rule.icon className={`h-5 w-5 ${rule.color}`} />
                </div>
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="text-sm font-semibold text-slate-100">{rule.name}</h3>
                    <StatusBadge
                      variant={rule.isActive ? 'success' : 'stopped'}
                      label={rule.isActive ? 'Active' : 'Disabled'}
                    />
                    <StatusBadge variant="info" label={rule.typeLabel} />
                    <StatusBadge
                      variant={rule.actionType === 'Hard Pause' ? 'danger' : 'warning'}
                      label={rule.actionType}
                    />
                  </div>
                  <p className="mt-1.5 text-xs text-slate-400">
                    <span className="font-medium text-slate-300">If: </span>
                    {rule.condition}
                  </p>
                  <p className="mt-1 text-xs text-slate-400">
                    <span className="font-medium text-slate-300">Then: </span>
                    {rule.action}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => toggleRule(rule.id)}
                  className="relative inline-flex h-6 w-11 shrink-0 cursor-pointer items-center rounded-full transition-colors duration-200 focus:outline-none"
                  style={{ backgroundColor: rule.isActive ? '#10b981' : '#334155' }}
                  title={rule.isActive ? 'Disable' : 'Enable'}
                  role="switch"
                  aria-checked={rule.isActive}
                >
                  <span
                    className="inline-block h-4 w-4 rounded-full bg-white shadow transition-transform duration-200"
                    style={{ transform: rule.isActive ? 'translateX(22px)' : 'translateX(4px)' }}
                  />
                </button>
                <button className="rounded-lg p-2 text-slate-400 transition-colors hover:bg-[#1a1a2e] hover:text-slate-200">
                  <Edit3 className="h-4 w-4" />
                </button>
                <button className="rounded-lg p-2 text-slate-400 transition-colors hover:bg-[#1a1a2e] hover:text-red-400">
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
