import { Wifi } from 'lucide-react'

export function ConnectionStatus() {
  return (
    <div className="flex items-center gap-2">
      <div className="h-2 w-2 rounded-full bg-emerald-500" />
      <Wifi className="h-3.5 w-3.5 text-emerald-400" />
      <span className="text-xs text-emerald-400">Live</span>
    </div>
  )
}
