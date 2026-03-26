import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  startSimulation,
  pauseSimulation,
  setSpeed,
  setScenario,
  triggerAnomaly,
  resetSimulation,
  fetchStatus,
  fetchLog,
} from '@/api/simulation'

export function useSimulationStatus() {
  return useQuery({
    queryKey: ['simulation', 'status'],
    queryFn: fetchStatus,
    refetchInterval: 5000,
  })
}

export function useSimulationLog(params?: { limit?: number; offset?: number; event_type?: string }) {
  return useQuery({
    queryKey: ['simulation', 'log', params],
    queryFn: () => fetchLog(params),
  })
}

export function useStartSimulation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (scenario?: string) => startSimulation(scenario),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['simulation', 'status'] })
    },
  })
}

export function usePauseSimulation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: pauseSimulation,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['simulation', 'status'] })
    },
  })
}

export function useSetSpeed() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (multiplier: 1 | 5 | 10) => setSpeed(multiplier),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['simulation', 'status'] })
    },
  })
}

export function useSetScenario() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (scenario: string) => setScenario(scenario),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['simulation', 'status'] })
    },
  })
}

export function useTriggerAnomaly() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (campaignId: string) => triggerAnomaly(campaignId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['simulation', 'log'] })
    },
  })
}

export function useResetSimulation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: resetSimulation,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['simulation'] })
    },
  })
}
