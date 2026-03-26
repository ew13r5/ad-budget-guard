import { Shield, FlaskConical, Rocket } from 'lucide-react'
import type { AccountMode } from '@/api/types'

const modeConfig = {
  sandbox: {
    label: 'Sandbox',
    icon: Shield,
    className: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  },
  simulation: {
    label: 'Simulation',
    icon: FlaskConical,
    className: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  },
  production: {
    label: 'Production',
    icon: Rocket,
    className: 'bg-red-500/10 text-red-400 border-red-500/20',
  },
}

export function ModeIndicator({ mode }: { mode: AccountMode }) {
  const config = modeConfig[mode]
  const Icon = config.icon

  return (
    <div className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium ${config.className}`}>
      <Icon className="h-3 w-3" />
      {config.label}
    </div>
  )
}
