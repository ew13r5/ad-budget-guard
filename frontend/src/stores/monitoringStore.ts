import { create } from 'zustand'
import type { WsTickCampaign } from '@/api/types'

interface MonitoringState {
  liveCampaigns: WsTickCampaign[]
  connectionStatus: 'connecting' | 'open' | 'closed'
  lastUpdate: string | null
  setLiveCampaigns: (campaigns: WsTickCampaign[]) => void
  setConnectionStatus: (status: 'connecting' | 'open' | 'closed') => void
  setLastUpdate: (time: string) => void
}

export const useMonitoringStore = create<MonitoringState>((set) => ({
  liveCampaigns: [],
  connectionStatus: 'closed',
  lastUpdate: null,

  setLiveCampaigns: (campaigns) => set({ liveCampaigns: campaigns }),
  setConnectionStatus: (status) => set({ connectionStatus: status }),
  setLastUpdate: (time) => set({ lastUpdate: time }),
}))
