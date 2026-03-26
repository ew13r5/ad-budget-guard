import type { ReactNode } from 'react'

interface EmptyStateProps {
  icon?: ReactNode
  title: string
  description: string
}

export function EmptyState({ icon, title, description }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-20">
      {icon && <div className="mb-4 text-slate-500">{icon}</div>}
      <h2 className="mb-2 text-xl font-semibold text-slate-300">{title}</h2>
      <p className="max-w-md text-center text-sm text-slate-500">{description}</p>
    </div>
  )
}
