import { create } from 'zustand'

interface UIState {
  sidebarOpen: boolean
  selectedAccountId: string | null
  theme: 'dark'
  campaignFilter: 'all' | 'active' | 'paused'
  toggleSidebar: () => void
  setSidebarOpen: (open: boolean) => void
  setSelectedAccountId: (id: string | null) => void
  setCampaignFilter: (filter: 'all' | 'active' | 'paused') => void
}

export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: true,
  selectedAccountId: null,
  theme: 'dark',
  campaignFilter: 'all',

  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  setSelectedAccountId: (id) => set({ selectedAccountId: id }),
  setCampaignFilter: (filter) => set({ campaignFilter: filter }),
}))
