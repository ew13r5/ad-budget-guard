import { AccountMode } from '@/api/types'

export const mockDashboardAccounts = [
  {
    id: 'acc-delta',
    name: 'Client-Delta',
    subtitle: 'Restaurant Chain',
    mode: AccountMode.production,
    spend: 892.00,
    budget: 150,
    alert: 'HARD PAUSED - Budget exceeded 5.9x',
    status: 'paused' as const,
  },
  {
    id: 'acc-gamma',
    name: 'Client-Gamma',
    subtitle: 'Real Estate Agency',
    mode: AccountMode.production,
    spend: 214.50,
    budget: 200,
    alert: '3 campaigns paused',
    status: 'paused' as const,
  },
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
    id: 'acc-epsilon',
    name: 'Client-Epsilon',
    subtitle: 'Online Education',
    mode: AccountMode.sandbox,
    spend: 12.30,
    budget: 500,
  },
]

export const mockAccountsPageAccounts = [
  {
    id: 'acc-alpha',
    name: 'Client-Alpha',
    subtitle: 'E-commerce Brand',
    mode: AccountMode.simulation,
    spend: 174.20,
    budget: 200,
    campaigns: 10,
    activeCampaigns: 8,
    pausedCampaigns: 2,
    alert: 'Approaching daily limit',
  },
  {
    id: 'acc-beta',
    name: 'Client-Beta',
    subtitle: 'SaaS Startup',
    mode: AccountMode.sandbox,
    spend: 89.40,
    budget: 350,
    campaigns: 8,
    activeCampaigns: 8,
    pausedCampaigns: 0,
  },
  {
    id: 'acc-gamma',
    name: 'Client-Gamma',
    subtitle: 'Real Estate Agency',
    mode: AccountMode.production,
    spend: 214.50,
    budget: 200,
    campaigns: 8,
    activeCampaigns: 5,
    pausedCampaigns: 3,
    alert: '3 campaigns paused',
    status: 'paused' as const,
  },
  {
    id: 'acc-delta',
    name: 'Client-Delta',
    subtitle: 'Restaurant Chain',
    mode: AccountMode.production,
    spend: 892.00,
    budget: 150,
    campaigns: 6,
    activeCampaigns: 0,
    pausedCampaigns: 6,
    alert: 'HARD PAUSED — Anomaly detected',
    status: 'paused' as const,
  },
  {
    id: 'acc-epsilon',
    name: 'Client-Epsilon',
    subtitle: 'Online Education',
    mode: AccountMode.sandbox,
    spend: 12.30,
    budget: 500,
    campaigns: 7,
    activeCampaigns: 4,
    pausedCampaigns: 0,
  },
]

export const mockForecastData = Array.from({ length: 24 }, (_, i) => {
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
