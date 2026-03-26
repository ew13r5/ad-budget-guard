import apiClient from './client'
import type {
  SimulationStartResponse,
  SimulationPauseResponse,
  SimulationSpeedResponse,
  SimulationScenarioResponse,
  SimulationTriggerAnomalyResponse,
  SimulationResetResponse,
  SimulationStatusResponse,
  SimulationLogResponse,
} from './types'

export async function startSimulation(scenario?: string): Promise<SimulationStartResponse> {
  const { data } = await apiClient.post<SimulationStartResponse>('/simulation/start', {
    scenario: scenario ?? 'normal',
  })
  return data
}

export async function pauseSimulation(): Promise<SimulationPauseResponse> {
  const { data } = await apiClient.post<SimulationPauseResponse>('/simulation/pause')
  return data
}

export async function setSpeed(multiplier: 1 | 5 | 10): Promise<SimulationSpeedResponse> {
  const { data } = await apiClient.put<SimulationSpeedResponse>('/simulation/speed', { multiplier })
  return data
}

export async function setScenario(scenario: string): Promise<SimulationScenarioResponse> {
  const { data } = await apiClient.put<SimulationScenarioResponse>('/simulation/scenario', { scenario })
  return data
}

export async function triggerAnomaly(campaignId: string): Promise<SimulationTriggerAnomalyResponse> {
  const { data } = await apiClient.post<SimulationTriggerAnomalyResponse>('/simulation/trigger-anomaly', {
    campaign_id: campaignId,
  })
  return data
}

export async function resetSimulation(): Promise<SimulationResetResponse> {
  const { data } = await apiClient.post<SimulationResetResponse>('/simulation/reset')
  return data
}

export async function fetchStatus(): Promise<SimulationStatusResponse> {
  const { data } = await apiClient.get<SimulationStatusResponse>('/simulation/status')
  return data
}

export async function fetchLog(params?: {
  limit?: number
  offset?: number
  event_type?: string
}): Promise<SimulationLogResponse> {
  const { data } = await apiClient.get<SimulationLogResponse>('/simulation/log', { params })
  return data
}
