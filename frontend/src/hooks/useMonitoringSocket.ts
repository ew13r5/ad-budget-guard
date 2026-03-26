import { useMonitoringStore } from '@/stores/monitoringStore'
import { useWebSocket } from './useWebSocket'

export function useMonitoringSocket() {
  const { status, send } = useWebSocket()
  const { liveCampaigns, lastUpdate, connectionStatus } = useMonitoringStore()

  return {
    status,
    connectionStatus,
    send,
    liveCampaigns,
    lastUpdate,
  }
}
