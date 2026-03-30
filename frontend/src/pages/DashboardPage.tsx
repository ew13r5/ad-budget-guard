import { useEffect, useMemo } from 'react'
import { AccountCard } from '@/components/accounts/AccountCard'
import { ForecastChart } from '@/components/charts/ForecastChart'
import { useAccounts } from '@/hooks/useAccounts'
import { useAccountsSpend } from '@/hooks/useAccountsSpend'
import { mockDashboardAccounts, mockForecastData } from '@/data/mockData'
import {
  Users,
  DollarSign,
  ShieldCheck,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  PauseCircle,
} from 'lucide-react'

export default function DashboardPage() {
  useEffect(() => { document.title = 'Dashboard | Ad Budget Guard' }, [])

  const { data: accountsData, isLoading, isError } = useAccounts()

  const accounts = accountsData?.accounts ?? []
  const accountIds = useMemo(() => accounts.map((a) => a.id), [accounts])
  const { data: spendData } = useAccountsSpend(accountIds)

  const isDemoMode = isError || (!isLoading && accounts.length === 0)

  // Build display data
  const displayAccounts = isDemoMode
    ? mockDashboardAccounts
    : accounts.map((account) => {
        const spend = spendData?.[account.id]
        return {
          id: account.id,
          name: account.name,
          subtitle: account.meta_account_id || account.mode,
          mode: account.mode,
          spend: spend ? parseFloat(spend.total_spend) : 0,
          budget: spend ? parseFloat(spend.daily_budget) : 0,
        }
      })

  const totalSpend = displayAccounts.reduce((s, a) => s + a.spend, 0)

  const stats = [
    {
      label: 'Total Accounts',
      value: String(displayAccounts.length),
      change: isDemoMode ? '+2 this month' : 'monitored',
      trend: 'up' as const,
      icon: Users,
      color: 'text-blue-400',
      bgColor: 'bg-blue-500/10',
    },
    {
      label: 'Total Spend Today',
      value: `$${totalSpend.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,
      change: isDemoMode ? '+12.3% vs yesterday' : 'across all accounts',
      trend: 'up' as const,
      icon: DollarSign,
      color: 'text-emerald-400',
      bgColor: 'bg-emerald-500/10',
    },
    {
      label: 'Active Rules',
      value: isDemoMode ? '12' : '--',
      change: isDemoMode ? '4 triggered today' : '',
      trend: 'up' as const,
      icon: ShieldCheck,
      color: 'text-purple-400',
      bgColor: 'bg-purple-500/10',
    },
    {
      label: 'Alerts Today',
      value: isDemoMode ? '7' : '--',
      change: isDemoMode ? '3 critical' : '',
      trend: 'down' as const,
      icon: AlertTriangle,
      color: 'text-red-400',
      bgColor: 'bg-red-500/10',
    },
    {
      label: 'Paused Campaigns',
      value: isDemoMode ? '9' : '--',
      change: isDemoMode ? 'across 2 accounts' : '',
      trend: 'down' as const,
      icon: PauseCircle,
      color: 'text-orange-400',
      bgColor: 'bg-orange-500/10',
    },
  ]

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-100">Dashboard</h1>
          <p className="mt-1 text-sm text-slate-500">
            Monitor your ad accounts and budget rules in real-time
          </p>
        </div>
        {isDemoMode && (
          <span className="rounded-full bg-amber-500/10 px-3 py-1 text-xs font-medium text-amber-400">
            Demo Mode
          </span>
        )}
      </div>

      {/* Stats row */}
      {isLoading ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="h-28 animate-pulse rounded-xl bg-[#1a1a2e]" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
          {stats.map((stat) => (
            <div
              key={stat.label}
              className="rounded-xl border border-[#1a1a2e] bg-[#12121a] p-5"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium uppercase tracking-wider text-slate-500">
                  {stat.label}
                </span>
                <div className={`rounded-lg p-2 ${stat.bgColor}`}>
                  <stat.icon className={`h-4 w-4 ${stat.color}`} />
                </div>
              </div>
              <p className="mt-2 text-3xl font-bold tracking-tight text-slate-100">
                {stat.value}
              </p>
              {stat.change && (
                <div className="mt-1 flex items-center gap-1 text-xs">
                  {stat.trend === 'up' ? (
                    <TrendingUp className="h-3 w-3 text-emerald-400" />
                  ) : (
                    <TrendingDown className="h-3 w-3 text-red-400" />
                  )}
                  <span className="text-slate-500">{stat.change}</span>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Account cards grid */}
      <div>
        <h2 className="mb-4 text-lg font-semibold text-slate-200">Ad Accounts</h2>
        {isLoading ? (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="h-40 animate-pulse rounded-xl bg-[#1a1a2e]" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
            {displayAccounts.map((account) => (
              <AccountCard key={account.id} {...account} />
            ))}
          </div>
        )}
      </div>

      {/* Forecast chart */}
      <ForecastChart data={mockForecastData} budget={200} />
    </div>
  )
}
