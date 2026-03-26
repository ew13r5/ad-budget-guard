const variants: Record<string, string> = {
  sandbox: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  simulation: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  production: 'bg-red-500/10 text-red-400 border-red-500/20',
  ACTIVE: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  PAUSED: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  running: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  paused: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  stopped: 'bg-slate-500/10 text-slate-400 border-slate-500/20',
  warning: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  danger: 'bg-red-500/10 text-red-400 border-red-500/20',
  success: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  info: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
}

interface StatusBadgeProps {
  variant: string
  label: string
  className?: string
}

export function StatusBadge({ variant, label, className = '' }: StatusBadgeProps) {
  const classes = variants[variant] ?? variants.info

  return (
    <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium ${classes} ${className}`}>
      {label}
    </span>
  )
}
