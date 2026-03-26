import { useState } from 'react'
import { StatusBadge } from '@/components/common/StatusBadge'
import {
  ShieldCheck,
  Plus,
  ToggleLeft,
  ToggleRight,
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
  condition: string
  action: string
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
    condition: 'When daily spend exceeds 95% of budget',
    action: 'Pause campaign and send alert',
    isActive: true,
    icon: DollarSign,
    color: 'text-emerald-400',
    bgColor: 'bg-emerald-500/10',
  },
  {
    id: 'r2',
    name: 'Monthly Budget Cap',
    type: 'monthly_limit',
    condition: 'When monthly spend exceeds $5,000 per account',
    action: 'Pause all campaigns in account',
    isActive: true,
    icon: Calendar,
    color: 'text-blue-400',
    bgColor: 'bg-blue-500/10',
  },
  {
    id: 'r3',
    name: 'Hourly Spend Rate Monitor',
    type: 'hourly_rate',
    condition: 'When hourly spend rate exceeds 2x the daily average',
    action: 'Reduce budget by 50% and alert',
    isActive: true,
    icon: Clock,
    color: 'text-purple-400',
    bgColor: 'bg-purple-500/10',
  },
  {
    id: 'r4',
    name: 'Anomaly Detection',
    type: 'anomaly',
    condition: 'When spend pattern deviates 3 sigma from historical norm',
    action: 'Hard pause campaign, require manual review',
    isActive: false,
    icon: Zap,
    color: 'text-amber-400',
    bgColor: 'bg-amber-500/10',
  },
]

export default function RulesPage() {
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
                  <div className="flex items-center gap-3">
                    <h3 className="text-sm font-semibold text-slate-100">{rule.name}</h3>
                    <StatusBadge
                      variant={rule.isActive ? 'success' : 'stopped'}
                      label={rule.isActive ? 'Active' : 'Disabled'}
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
                  className="rounded-lg p-2 text-slate-400 transition-colors hover:bg-[#1a1a2e] hover:text-slate-200"
                  title={rule.isActive ? 'Disable' : 'Enable'}
                >
                  {rule.isActive ? (
                    <ToggleRight className="h-5 w-5 text-emerald-400" />
                  ) : (
                    <ToggleLeft className="h-5 w-5" />
                  )}
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
