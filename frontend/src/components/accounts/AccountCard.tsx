import { Link } from 'react-router-dom'
import { SpendProgressBar } from './SpendProgressBar'
import { ModeIndicator } from '@/components/common/ModeIndicator'
import { TrendingUp, AlertTriangle, Pause } from 'lucide-react'
import type { AccountMode } from '@/api/types'

interface AccountCardProps {
  id: string
  name: string
  subtitle: string
  mode: AccountMode
  spend: number
  budget: number
  status?: string
  alert?: string
}

export function AccountCard({
  id,
  name,
  subtitle,
  mode,
  spend,
  budget,
  status,
  alert,
}: AccountCardProps) {
  const percent = budget > 0 ? (spend / budget) * 100 : 0
  const isOverBudget = percent > 100
  const isCritical = percent > 200

  return (
    <Link
      to={`/accounts/${id}`}
      className={`group block rounded-xl border transition-all duration-200 hover:shadow-lg hover:shadow-blue-500/5 ${
        isCritical
          ? 'border-red-500/30 bg-red-500/5 hover:border-red-500/50'
          : isOverBudget
            ? 'border-red-500/20 bg-[#12121a] hover:border-red-500/30'
            : 'border-[#1a1a2e] bg-[#12121a] hover:border-[#2a2a3e]'
      }`}
    >
      <div className="p-5">
        {/* Header */}
        <div className="mb-4 flex items-start justify-between">
          <div className="min-w-0 flex-1">
            <h3 className="truncate text-sm font-semibold text-slate-100 group-hover:text-white">
              {name}
            </h3>
            <p className="mt-0.5 text-xs text-slate-500">{subtitle}</p>
          </div>
          <ModeIndicator mode={mode} />
        </div>

        {/* Spend info */}
        <div className="mb-3 flex items-baseline justify-between">
          <div className="flex items-baseline gap-1">
            <span className="text-2xl font-bold tracking-tight text-slate-100">
              ${spend.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </span>
            <span className="text-xs text-slate-500">
              / ${budget.toLocaleString('en-US', { minimumFractionDigits: 0 })}
            </span>
          </div>
          <div className="flex items-center gap-1 text-xs text-slate-500">
            <TrendingUp className="h-3 w-3" />
            today
          </div>
        </div>

        {/* Progress bar */}
        <SpendProgressBar percent={percent} />

        {/* Alert */}
        {alert && (
          <div className={`mt-3 flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-medium ${
            isCritical
              ? 'bg-red-500/10 text-red-400'
              : 'bg-amber-500/10 text-amber-400'
          }`}>
            {status === 'paused' ? (
              <Pause className="h-3 w-3" />
            ) : (
              <AlertTriangle className="h-3 w-3" />
            )}
            {alert}
          </div>
        )}
      </div>
    </Link>
  )
}
