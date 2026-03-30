import { useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { AccountCard } from '@/components/accounts/AccountCard'
import { useAccounts } from '@/hooks/useAccounts'
import { useAccountsSpend } from '@/hooks/useAccountsSpend'
import { mockAccountsPageAccounts } from '@/data/mockData'
import { Users } from 'lucide-react'

export default function AccountsPage() {
  const navigate = useNavigate()

  useEffect(() => { document.title = 'Accounts | Ad Budget Guard' }, [])

  const { data: accountsData, isLoading, isError } = useAccounts()

  const accounts = accountsData?.accounts ?? []
  const accountIds = useMemo(() => accounts.map((a) => a.id), [accounts])
  const { data: spendData } = useAccountsSpend(accountIds)

  const isDemoMode = isError || (!isLoading && accounts.length === 0)

  const displayAccounts = isDemoMode
    ? mockAccountsPageAccounts
    : accounts.map((account) => {
        const spend = spendData?.[account.id]
        return {
          id: account.id,
          name: account.name,
          subtitle: account.meta_account_id || account.mode,
          mode: account.mode,
          spend: spend ? parseFloat(spend.total_spend) : 0,
          budget: spend ? parseFloat(spend.daily_budget) : 0,
        }
      })

  const totalSpend = displayAccounts.reduce((s, a) => s + a.spend, 0)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Accounts</h1>
          <p className="text-sm text-slate-400 mt-1">
            {displayAccounts.length} accounts monitored
          </p>
        </div>
        {isDemoMode && (
          <span className="rounded-full bg-amber-500/10 px-3 py-1 text-xs font-medium text-amber-400">
            Demo Mode
          </span>
        )}
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="h-40 animate-pulse rounded-xl bg-[#1a1a2e]" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
          {displayAccounts.map((account) => (
            <div
              key={account.id}
              onClick={() => navigate(`/accounts/${account.id}`)}
              className="cursor-pointer"
            >
              <AccountCard
                id={account.id}
                name={account.name}
                subtitle={account.subtitle}
                mode={account.mode}
                spend={account.spend}
                budget={account.budget}
                alert={'alert' in account ? (account as any).alert : undefined}
                status={'status' in account ? (account as any).status : undefined}
              />
            </div>
          ))}
        </div>
      )}

      {/* Summary */}
      <div className="rounded-xl border border-[#1a1a2e] bg-[#12121a] p-5">
        <div className="flex items-center gap-2 mb-4">
          <Users className="h-4 w-4 text-blue-400" />
          <span className="text-sm font-medium text-slate-300">Account Summary</span>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
          <div>
            <div className="text-2xl font-bold text-slate-100">{displayAccounts.length}</div>
            <div className="text-xs text-slate-500">Total Accounts</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-emerald-400">
              {displayAccounts.filter((a) => !('status' in a && (a as any).status === 'paused')).length}
            </div>
            <div className="text-xs text-slate-500">Active</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-red-400">
              {displayAccounts.filter((a) => 'status' in a && (a as any).status === 'paused').length}
            </div>
            <div className="text-xs text-slate-500">With Paused Campaigns</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-slate-100">
              ${totalSpend.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </div>
            <div className="text-xs text-slate-500">Total Spend Today</div>
          </div>
        </div>
      </div>
    </div>
  )
}
