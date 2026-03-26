import apiClient from './client'

export interface SpendData {
  account_id: string
  total_spend: string
  daily_budget: string
  percent: number
  timestamp: string
}

export interface ForecastData {
  account_id: string
  forecast_spend: string
  confidence: number
  timestamp: string
  data_points: Array<{ time: string; value: number }>
}

export async function fetchSpend(accountId?: string): Promise<SpendData[]> {
  const params = accountId ? { account_id: accountId } : {}
  const { data } = await apiClient.get<SpendData[]>('/monitoring/spend', { params })
  return data
}

export async function fetchForecast(accountId: string): Promise<ForecastData> {
  const { data } = await apiClient.get<ForecastData>(`/monitoring/forecast/${accountId}`)
  return data
}
