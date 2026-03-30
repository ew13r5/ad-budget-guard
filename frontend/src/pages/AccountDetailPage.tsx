import { useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { CampaignTable } from '@/components/campaigns/CampaignTable'
import { ForecastChart } from '@/components/charts/ForecastChart'
import { ModeIndicator } from '@/components/common/ModeIndicator'
import { SpendProgressBar } from '@/components/accounts/SpendProgressBar'
import { AccountMode } from '@/api/types'
import { ArrowLeft, ExternalLink, TrendingUp, Clock } from 'lucide-react'

const fmt = (v: number) =>
  new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(v)

// Mock campaigns for Client-Alpha
const mockCampaigns = [
  { id: 'c1', name: 'Summer Sale - Broad', status: 'ACTIVE' as const, dailyBudget: 25, spend: 22.40, spendPercent: 89.6, forecast: 27.80 },
  { id: 'c2', name: 'Retargeting - Cart Abandoners', status: 'ACTIVE' as const, dailyBudget: 30, spend: 18.50, spendPercent: 61.7, forecast: 28.30 },
  { id: 'c3', name: 'Lookalike - Top Customers', status: 'ACTIVE' as const, dailyBudget: 20, spend: 19.80, spendPercent: 99.0, forecast: 24.50 },
  { id: 'c4', name: 'Brand Awareness - Video', status: 'ACTIVE' as const, dailyBudget: 15, spend: 12.30, spendPercent: 82.0, forecast: 16.40 },
  { id: 'c5', name: 'Product Catalog - DPA', status: 'PAUSED' as const, dailyBudget: 35, spend: 34.20, spendPercent: 97.7, forecast: 35.00 },
  { id: 'c6', name: 'Flash Sale - Urgency', status: 'ACTIVE' as const, dailyBudget: 10, spend: 8.90, spendPercent: 89.0, forecast: 11.20 },
  { id: 'c7', name: 'Newsletter Subscribers', status: 'ACTIVE' as const, dailyBudget: 12, spend: 7.60, spendPercent: 63.3, forecast: 10.50 },
  { id: 'c8', name: 'Instagram Stories', status: 'ACTIVE' as const, dailyBudget: 18, spend: 16.20, spendPercent: 90.0, forecast: 19.80 },
  { id: 'c9', name: 'Seasonal - Back to School', status: 'PAUSED' as const, dailyBudget: 20, spend: 19.50, spendPercent: 97.5, forecast: 20.00 },
  { id: 'c10', name: 'Competitor Targeting', status: 'ACTIVE' as const, dailyBudget: 15, spend: 14.80, spendPercent: 98.7, forecast: 17.60 },
]

const mockAccounts: Record<string, {
  name: string; subtitle: string; metaId: string; mode: AccountMode
  dailyBudget: number; monthlyBudget: number; spendToday: number; spendMonth: number
}> = {
  'acc-alpha': { name: 'Client-Alpha', subtitle: 'E-commerce Brand', metaId: 'act_123456789', mode: AccountMode.simulation, dailyBudget: 200, monthlyBudget: 5000, spendToday: 174.20, spendMonth: 3420.80 },
  'acc-beta': { name: 'Client-Beta', subtitle: 'SaaS Startup', metaId: 'act_987654321', mode: AccountMode.sandbox, dailyBudget: 350, monthlyBudget: 8000, spendToday: 89.40, spendMonth: 2145.60 },
  'acc-gamma': { name: 'Client-Gamma', subtitle: 'Real Estate Agency', metaId: 'act_456789123', mode: AccountMode.production, dailyBudget: 200, monthlyBudget: 5000, spendToday: 214.50, spendMonth: 4180.30 },
  'acc-delta': { name: 'Client-Delta', subtitle: 'Restaurant Chain', metaId: 'act_789123456', mode: AccountMode.production, dailyBudget: 150, monthlyBudget: 3500, spendToday: 892.00, spendMonth: 3280.50 },
  'acc-epsilon': { name: 'Client-Epsilon', subtitle: 'Online Education', metaId: 'act_321654987', mode: AccountMode.sandbox, dailyBudget: 500, monthlyBudget: 12000, spendToday: 12.30, spendMonth: 298.40 },
}

const forecastData = Array.from({ length: 24 }, (_, i) => {
  const hour = i
  const time = `${hour.toString().padStart(2, '0')}:00`
  const base = 7.5 * hour + Math.sin(hour * 0.4) * 12
  const actual = hour <= 14 ? Math.max(0, base + (Math.random() - 0.3) * 8) : 0
  const forecast = hour >= 13 ? base + (Math.random() - 0.5) * 5 : undefined
  return { time, actual: Math.round(actual * 100) / 100, forecast: forecast ? Math.round(forecast * 100) / 100 : undefined }
})

export default function AccountDetailPage() {
  const { id } = useParams<{ id: string }>()
  const account = mockAccounts[id || ''] || mockAccounts['acc-alpha']

  useEffect(() => {
    document.title = `${account.name} | Ad Budget Guard`
  }, [account.name])

  const dailyPercent = account.dailyBudget > 0 ? (account.spendToday / account.dailyBudget) * 100 : 0
  const monthlyPercent = account.monthlyBudget > 0 ? (account.spendMonth / account.monthlyBudget) * 100 : 0

  // Forecast calculations
  const hoursElapsed = 14 // simulated current hour
  const hourlyRate = hoursElapsed > 0 ? account.spendToday / hoursElapsed : 0
  const eodForecast = hourlyRate * 24
  const forecastPercent = account.dailyBudget > 0 ? (eodForecast / account.dailyBudget) * 100 : 0
  const forecastColor = forecastPercent > 100 ? 'text-red-400' : forecastPercent > 80 ? 'text-amber-400' : 'text-emerald-400'

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-4">
          <Link
            to="/accounts"
            className="rounded-lg p-2 text-slate-400 transition-colors hover:bg-[#1a1a2e] hover:text-slate-200"
          >
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold tracking-tight text-slate-100">
                {account.name}
              </h1>
              <ModeIndicator mode={account.mode} />
            </div>
            <div className="mt-1 flex items-center gap-2 text-sm text-slate-500">
              <span>{account.subtitle}</span>
              <span className="text-slate-600">|</span>
              <span className="flex items-center gap-1 font-mono text-xs">
                {account.metaId}
                <ExternalLink className="h-3 w-3" />
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Spend Summary */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {/* Today vs Daily Limit */}
        <div className="rounded-xl border border-[#1a1a2e] bg-[#12121a] p-5">
          <div className="mb-3 flex items-center justify-between">
            <span className="text-xs font-medium uppercase tracking-wider text-slate-500">Today vs Daily Limit</span>
            <span className="text-xs text-slate-500">{dailyPercent.toFixed(1)}%</span>
          </div>
          <div className="mb-2 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-slate-100">{fmt(account.spendToday)}</span>
            <span className="text-sm text-slate-500">/ {fmt(account.dailyBudget)}</span>
          </div>
          <SpendProgressBar percent={dailyPercent} />
        </div>

        {/* Month vs Monthly Limit */}
        <div className="rounded-xl border border-[#1a1a2e] bg-[#12121a] p-5">
          <div className="mb-3 flex items-center justify-between">
            <span className="text-xs font-medium uppercase tracking-wider text-slate-500">Month vs Monthly Limit</span>
            <span className="text-xs text-slate-500">{monthlyPercent.toFixed(1)}%</span>
          </div>
          <div className="mb-2 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-slate-100">{fmt(account.spendMonth)}</span>
            <span className="text-sm text-slate-500">/ {fmt(account.monthlyBudget)}</span>
          </div>
          <SpendProgressBar percent={monthlyPercent} />
        </div>
      </div>

      {/* Forecast Section */}
      <div className="rounded-xl border border-[#1a1a2e] bg-[#12121a] p-5">
        <h3 className="mb-4 text-sm font-semibold text-slate-200">Spend Forecast</h3>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div className="flex items-center gap-3 rounded-lg border border-[#1a1a2e] p-4">
            <div className="rounded-lg bg-blue-500/10 p-2">
              <Clock className="h-4 w-4 text-blue-400" />
            </div>
            <div>
              <p className="text-xs text-slate-500">Hourly Rate</p>
              <p className="text-lg font-bold text-slate-100">{fmt(hourlyRate)}<span className="text-xs font-normal text-slate-500">/hr</span></p>
            </div>
          </div>
          <div className="flex items-center gap-3 rounded-lg border border-[#1a1a2e] p-4">
            <div className="rounded-lg bg-purple-500/10 p-2">
              <TrendingUp className={`h-4 w-4 ${forecastColor}`} />
            </div>
            <div>
              <p className="text-xs text-slate-500">EOD Forecast</p>
              <p className={`text-lg font-bold ${forecastColor}`}>{fmt(eodForecast)}</p>
            </div>
          </div>
          <div className="flex items-center gap-3 rounded-lg border border-[#1a1a2e] p-4">
            <div className={`rounded-lg p-2 ${forecastPercent > 100 ? 'bg-red-500/10' : forecastPercent > 80 ? 'bg-amber-500/10' : 'bg-emerald-500/10'}`}>
              <TrendingUp className={`h-4 w-4 ${forecastColor}`} />
            </div>
            <div>
              <p className="text-xs text-slate-500">Forecast vs Budget</p>
              <p className={`text-lg font-bold ${forecastColor}`}>{forecastPercent.toFixed(1)}%</p>
            </div>
          </div>
        </div>
      </div>

      {/* Campaign table */}
      <div>
        <h2 className="mb-4 text-lg font-semibold text-slate-200">Campaigns</h2>
        <CampaignTable campaigns={mockCampaigns} />
      </div>

      {/* Forecast chart */}
      <ForecastChart data={forecastData} budget={account.dailyBudget} />
    </div>
  )
}
