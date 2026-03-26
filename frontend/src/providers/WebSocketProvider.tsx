import { createContext, useEffect, useRef, useState, useCallback, type ReactNode } from 'react'
import { useAuthStore } from '@/stores/authStore'
import { useMonitoringStore } from '@/stores/monitoringStore'
import { queryClient } from './QueryProvider'
import type { WsMessage, WsTickCampaign } from '@/api/types'

export interface WebSocketContextValue {
  status: 'connecting' | 'open' | 'closed'
  send: (data: string) => void
}

export const WebSocketContext = createContext<WebSocketContextValue | null>(null)

export function WebSocketProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<'connecting' | 'open' | 'closed'>('closed')
  const wsRef = useRef<WebSocket | null>(null)
  const retryCountRef = useRef(0)
  const retryTimerRef = useRef<ReturnType<typeof setTimeout>>(undefined)
  const pingTimerRef = useRef<ReturnType<typeof setInterval>>(undefined)
  const pendingTickRef = useRef<WsTickCampaign[] | null>(null)
  const rafIdRef = useRef<number | null>(null)

  const { accessToken } = useAuthStore()
  const { setLiveCampaigns, setConnectionStatus, setLastUpdate } = useMonitoringStore()

  const send = useCallback((data: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(data)
    }
  }, [])

  useEffect(() => {
    const wsUrl = import.meta.env.VITE_WS_URL || `ws://${window.location.host}/ws`

    function connect() {
      const url = accessToken ? `${wsUrl}/monitoring?token=${accessToken}` : `${wsUrl}/monitoring`

      setStatus('connecting')
      setConnectionStatus('connecting')

      const ws = new WebSocket(url)
      wsRef.current = ws

      ws.onopen = () => {
        setStatus('open')
        setConnectionStatus('open')
        retryCountRef.current = 0

        // Start ping interval
        pingTimerRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'ping' }))
          }
        }, 30000)

        // Invalidate all queries on reconnect
        queryClient.invalidateQueries()
      }

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data) as WsMessage

          switch (message.type) {
            case 'state_snapshot':
              queryClient.setQueryData(['simulation', 'status'], message)
              break

            case 'tick_update':
              // Batch high-frequency updates with rAF
              pendingTickRef.current = message.campaigns
              setLastUpdate(message.sim_time)
              if (!rafIdRef.current) {
                rafIdRef.current = requestAnimationFrame(() => {
                  if (pendingTickRef.current) {
                    queryClient.setQueryData(['campaigns', 'live'], pendingTickRef.current)
                    setLiveCampaigns(pendingTickRef.current)
                  }
                  rafIdRef.current = null
                })
              }
              // Sliding window for chart data
              queryClient.setQueryData(
                ['simulation', 'ticks'],
                (old: Array<{ sim_time: string; campaigns: WsTickCampaign[] }> | undefined) =>
                  [...(old ?? []), { sim_time: message.sim_time, campaigns: message.campaigns }].slice(-60)
              )
              break

            case 'sim_event':
              queryClient.invalidateQueries({ queryKey: ['campaigns'] })
              queryClient.invalidateQueries({ queryKey: ['accounts'] })
              queryClient.invalidateQueries({ queryKey: ['simulation', 'log'] })
              break
          }
        } catch {
          // Skip malformed messages
        }
      }

      ws.onclose = () => {
        setStatus('connecting')
        setConnectionStatus('connecting')
        clearInterval(pingTimerRef.current)

        if (retryCountRef.current < 10) {
          const delay = Math.min(500 * Math.pow(2, retryCountRef.current), 30000) + Math.random() * 500
          retryCountRef.current++
          retryTimerRef.current = setTimeout(connect, delay)
        } else {
          setStatus('closed')
          setConnectionStatus('closed')
        }
      }

      ws.onerror = () => {
        // onclose fires after onerror
      }
    }

    connect()

    return () => {
      retryCountRef.current = 10 // prevent reconnect on unmount
      clearTimeout(retryTimerRef.current)
      clearInterval(pingTimerRef.current)
      if (rafIdRef.current) cancelAnimationFrame(rafIdRef.current)
      wsRef.current?.close()
    }
  }, [accessToken, setConnectionStatus, setLastUpdate, setLiveCampaigns])

  return (
    <WebSocketContext.Provider value={{ status, send }}>
      {children}
    </WebSocketContext.Provider>
  )
}
