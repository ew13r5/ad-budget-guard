import { AccountCard } from '@/components/accounts/AccountCard'
import { ForecastChart } from '@/components/charts/ForecastChart'
import { AccountMode } from '@/api/types'
import {
  Users,
  DollarSign,
  ShieldCheck,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
} from 'lucide-react'

// Mock account data for portfolio display
const mockAccounts = [
  {
    id: 'acc-alpha',
    name: 'Client-Alpha',
    subtitle: 'E-commerce Brand',
    mode: AccountMode.simulation,
    spend: 174.20,
    budget: 200,
    alert: 'Approaching daily limit',
  },
  {
    id: 'acc-beta',
    name: 'Client-Beta',
    subtitle: 'SaaS Startup',
    mode: AccountMode.sandbox,
    spend: 89.40,
    budget: 350,
  },
  {
    id: 'acc-gamma',
    name: 'Client-Gamma',
    subtitle: 'Real Estate Agency',
    mode: AccountMode.production,
    spend: 214.50,
    budget: 200,
    alert: '3 campaigns paused',
    status: 'paused',
  },
  {
    id: 'acc-delta',
    name: 'Client-Delta',
    subtitle: 'Restaurant Chain',
    mode: AccountMode.production,
    spend: 892.00,
    budget: 150,
    alert: 'HARD PAUSED - Budget exceeded 5.9x',
    status: 'paused',
  },
  {
    id: 'acc-epsilon',
    name: 'Client-Epsilon',
    subtitle: 'Online Education',
    mode: AccountMode.sandbox,
    spend: 12.30,
    budget: 500,
  },
]

// Mock forecast data
const forecastData = Array.from({ length: 24 }, (_, i) => {
  const hour = i
  const time = `${hour.toString().padStart(2, '0')}:00`
  const base = 8.5 * hour + Math.sin(hour * 0.5) * 15
  const actual = hour <= 14 ? Math.max(0, base + (Math.random() - 0.3) * 10) : undefined
  const forecast = hour >= 13 ? base + (Math.random() - 0.5) * 5 : undefined
  return {
    time,
    actual: actual !== undefined ? Math.round(actual * 100) / 100 : 0,
    forecast: forecast !== undefined ? Math.round(forecast * 100) / 100 : undefined,
  }
})

const stats = [
  {
    label: 'Total Accounts',
    value: '5',
    change: '+2 this month',
    trend: 'up' as const,
    icon: Users,
    color: 'text-blue-400',
    bgColor: 'bg-blue-500/10',
  },
  {
    label: 'Total Spend Today',
    value: '$1,382.40',
    change: '+12.3% vs yesterday',
    trend: 'up' as const,
    icon: DollarSign,
    color: 'text-emerald-400',
    bgColor: 'bg-emerald-500/10',
  },
  {
    label: 'Active Rules',
    value: '12',
    change: '4 triggered today',
    trend: 'up' as const,
    icon: ShieldCheck,
    color: 'text-purple-400',
    bgColor: 'bg-purple-500/10',
  },
  {
    label: 'Alerts Today',
    value: '7',
    change: '3 critical',
    trend: 'down' as const,
    icon: AlertTriangle,
    color: 'text-red-400',
    bgColor: 'bg-red-500/10',
  },
]

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-100">Dashboard</h1>
        <p className="mt-1 text-sm text-slate-500">
          Monitor your ad accounts and budget rules in real-time
        </p>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
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
            <div className="mt-1 flex items-center gap-1 text-xs">
              {stat.trend === 'up' ? (
                <TrendingUp className="h-3 w-3 text-emerald-400" />
              ) : (
                <TrendingDown className="h-3 w-3 text-red-400" />
              )}
              <span className="text-slate-500">{stat.change}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Account cards grid */}
      <div>
        <h2 className="mb-4 text-lg font-semibold text-slate-200">Ad Accounts</h2>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {mockAccounts.map((account) => (
            <AccountCard key={account.id} {...account} />
          ))}
        </div>
      </div>

      {/* Forecast chart */}
      <ForecastChart data={forecastData} budget={200} />
    </div>
  )
}
