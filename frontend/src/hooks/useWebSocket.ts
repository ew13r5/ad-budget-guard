import { useContext } from 'react'
import { WebSocketContext } from '@/providers/WebSocketProvider'
import type { WebSocketContextValue } from '@/providers/WebSocketProvider'

export function useWebSocket(): WebSocketContextValue {
  const context = useContext(WebSocketContext)
  if (!context) {
    throw new Error('useWebSocket must be used within WebSocketProvider')
  }
  return context
}
