import { useState, useMemo } from 'react'
import { CampaignRow } from './CampaignRow'
import { ArrowUpDown } from 'lucide-react'

interface Campaign {
  id: string
  name: string
  status: 'ACTIVE' | 'PAUSED'
  dailyBudget: number
  spend: number
  spendPercent: number
  forecast: number
}

interface CampaignTableProps {
  campaigns: Campaign[]
}

type SortKey = 'name' | 'status' | 'dailyBudget' | 'spend' | 'spendPercent' | 'forecast'

export function CampaignTable({ campaigns }: CampaignTableProps) {
  const [sortKey, setSortKey] = useState<SortKey>('spendPercent')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc')
  const [filter, setFilter] = useState<'all' | 'active' | 'paused'>('all')

  const filtered = useMemo(() => {
    let list = [...campaigns]
    if (filter === 'active') list = list.filter((c) => c.status === 'ACTIVE')
    if (filter === 'paused') list = list.filter((c) => c.status === 'PAUSED')
    list.sort((a, b) => {
      const aVal = a[sortKey]
      const bVal = b[sortKey]
      if (typeof aVal === 'string' && typeof bVal === 'string') {
        return sortDir === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal)
      }
      return sortDir === 'asc' ? Number(aVal) - Number(bVal) : Number(bVal) - Number(aVal)
    })
    return list
  }, [campaigns, filter, sortKey, sortDir])

  function handleSort(key: SortKey) {
    if (sortKey === key) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortKey(key)
      setSortDir('desc')
    }
  }

  const headers: { key: SortKey; label: string; align?: string }[] = [
    { key: 'name', label: 'Campaign Name' },
    { key: 'status', label: 'Status' },
    { key: 'dailyBudget', label: 'Daily Budget', align: 'text-right' },
    { key: 'spend', label: 'Spend', align: 'text-right' },
    { key: 'spendPercent', label: 'Usage' },
    { key: 'forecast', label: 'Forecast', align: 'text-right' },
  ]

  return (
    <div className="rounded-xl border border-[#1a1a2e] bg-[#12121a]">
      {/* Filter bar */}
      <div className="flex items-center gap-2 border-b border-[#1a1a2e] px-4 py-3">
        {(['all', 'active', 'paused'] as const).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
              filter === f
                ? 'bg-blue-600/10 text-blue-400'
                : 'text-slate-400 hover:bg-[#1a1a2e] hover:text-slate-200'
            }`}
          >
            {f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
        <span className="ml-auto text-xs text-slate-500">{filtered.length} campaigns</span>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-[#1a1a2e]">
              {headers.map((h) => (
                <th
                  key={h.key}
                  onClick={() => handleSort(h.key)}
                  className={`cursor-pointer px-4 py-3 text-xs font-medium uppercase tracking-wider text-slate-500 hover:text-slate-300 ${h.align || 'text-left'}`}
                >
                  <span className="inline-flex items-center gap-1">
                    {h.label}
                    <ArrowUpDown className="h-3 w-3" />
                  </span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.map((c) => (
              <CampaignRow key={c.id} {...c} />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
