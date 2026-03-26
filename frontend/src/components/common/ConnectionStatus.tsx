import { useMonitoringStore } from '@/stores/monitoringStore'
import { Wifi, WifiOff } from 'lucide-react'

export function ConnectionStatus() {
  const status = useMonitoringStore((s) => s.connectionStatus)

  const config = {
    open: {
      dot: 'bg-emerald-500',
      text: 'Connected',
      icon: Wifi,
      textColor: 'text-emerald-400',
    },
    connecting: {
      dot: 'bg-amber-500 animate-pulse',
      text: 'Reconnecting...',
      icon: Wifi,
      textColor: 'text-amber-400',
    },
    closed: {
      dot: 'bg-red-500',
      text: 'Disconnected',
      icon: WifiOff,
      textColor: 'text-red-400',
    },
  }[status]

  const Icon = config.icon

  return (
    <div className="flex items-center gap-2">
      <div className={`h-2 w-2 rounded-full ${config.dot}`} />
      <Icon className={`h-3.5 w-3.5 ${config.textColor}`} />
      <span className={`text-xs ${config.textColor}`}>{config.text}</span>
    </div>
  )
}
