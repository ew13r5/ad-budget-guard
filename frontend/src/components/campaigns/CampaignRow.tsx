import { StatusBadge } from '@/components/common/StatusBadge'
import { SpendProgressBar } from '@/components/accounts/SpendProgressBar'

interface CampaignRowProps {
  name: string
  status: 'ACTIVE' | 'PAUSED'
  dailyBudget: number
  spend: number
  spendPercent: number
  forecast: number
}

export function CampaignRow({ name, status, dailyBudget, spend, spendPercent, forecast }: CampaignRowProps) {
  return (
    <tr className="border-b border-[#1a1a2e] transition-colors hover:bg-[#1a1a2e]/50">
      <td className="px-4 py-3">
        <span className="text-sm font-medium text-slate-200">{name}</span>
      </td>
      <td className="px-4 py-3">
        <StatusBadge variant={status} label={status} />
      </td>
      <td className="px-4 py-3 text-right text-sm text-slate-300">
        ${dailyBudget.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
      </td>
      <td className="px-4 py-3 text-right text-sm text-slate-300">
        ${spend.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
      </td>
      <td className="w-40 px-4 py-3">
        <SpendProgressBar percent={spendPercent} showLabel={false} />
      </td>
      <td className="px-4 py-3 text-right text-sm text-slate-400">
        ${forecast.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
      </td>
    </tr>
  )
}
