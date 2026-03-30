import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { discoverAccounts, importCampaigns } from '@/api/auth'
import type { DiscoveredAccount } from '@/api/types'
import apiClient from '@/api/client'
import { toast } from 'sonner'
import {
  CheckCircle2,
  ChevronRight,
  ChevronLeft,
  Bell,
  Loader2,
  Rocket,
} from 'lucide-react'

interface RulePreset {
  type: string
  label: string
  threshold: number
  action: string
  enabled: boolean
}

const DEFAULT_RULES: RulePreset[] = [
  { type: 'daily_limit', label: 'Daily Budget Limit', threshold: 500, action: 'soft_pause', enabled: true },
  { type: 'monthly_limit', label: 'Monthly Budget Limit', threshold: 10000, action: 'hard_pause', enabled: true },
  { type: 'anomaly', label: 'Anomaly Detection (3x average)', threshold: 3, action: 'hard_pause', enabled: true },
]

const STEPS = ['Select Accounts', 'Set Rules', 'Configure Alerts', 'Review & Activate']

export default function OnboardingPage() {
  const navigate = useNavigate()
  const [step, setStep] = useState(1)
  const [loading, setLoading] = useState(true)
  const [activating, setActivating] = useState(false)
  const [accounts, setAccounts] = useState<DiscoveredAccount[]>([])
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [rules, setRules] = useState<RulePreset[]>(DEFAULT_RULES)
  const [applyToAll, setApplyToAll] = useState(true)
  const [alertConfig, setAlertConfig] = useState({
    telegramChatId: '',
    telegramBotToken: '',
    email: '',
  })

  useEffect(() => {
    document.title = 'Setup | Ad Budget Guard'
    discoverAccounts()
      .then((res) => {
        setAccounts(res.accounts)
        setSelectedIds(new Set(res.accounts.map((a) => a.id)))
      })
      .catch(() => toast.error('Failed to discover accounts'))
      .finally(() => setLoading(false))
  }, [])

  const toggleAccount = (id: string) => {
    const next = new Set(selectedIds)
    next.has(id) ? next.delete(id) : next.add(id)
    setSelectedIds(next)
  }

  const selectAll = () => setSelectedIds(new Set(accounts.map((a) => a.id)))
  const deselectAll = () => setSelectedIds(new Set())

  const toggleRule = (idx: number) => {
    const next = [...rules]
    next[idx] = { ...next[idx], enabled: !next[idx].enabled }
    setRules(next)
  }

  const updateThreshold = (idx: number, val: number) => {
    const next = [...rules]
    next[idx] = { ...next[idx], threshold: val }
    setRules(next)
  }

  const handleActivate = async () => {
    setActivating(true)
    try {
      const selectedAccounts = accounts.filter((a) => selectedIds.has(a.id))
      const enabledRules = rules.filter((r) => r.enabled)

      // Create rules for each account
      for (const account of selectedAccounts) {
        // Import campaigns
        try {
          await importCampaigns(account.id)
        } catch { /* non-critical */ }

        // Create rules
        for (const rule of enabledRules) {
          try {
            await apiClient.post(`/rules/${account.id}`, {
              rule_type: rule.type,
              threshold: rule.threshold,
              action: rule.action,
            })
          } catch { /* continue */ }
        }

        // Configure alerts
        if (alertConfig.telegramChatId) {
          try {
            await apiClient.put(`/alerts/config/${account.id}`, {
              channel: 'telegram',
              destination: alertConfig.telegramChatId,
              is_enabled: true,
              severity_filter: 'warning',
            })
          } catch { /* continue */ }
        }
        if (alertConfig.email) {
          try {
            await apiClient.put(`/alerts/config/${account.id}`, {
              channel: 'email',
              destination: alertConfig.email,
              is_enabled: true,
              severity_filter: 'warning',
            })
          } catch { /* continue */ }
        }
      }

      toast.success('Monitoring activated! Redirecting to dashboard...')
      setTimeout(() => navigate('/'), 1000)
    } catch {
      toast.error('Failed to activate monitoring')
    } finally {
      setActivating(false)
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#0a0a12]">
        <Loader2 className="h-8 w-8 animate-spin text-blue-400" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-[#0a0a12] px-4 py-8">
      <div className="mx-auto max-w-3xl">
        {/* Header */}
        <div className="mb-8 text-center">
          <h1 className="text-2xl font-bold text-slate-100">Welcome to Ad Budget Guard</h1>
          <p className="mt-2 text-sm text-slate-500">Let's set up your monitoring in 4 easy steps</p>
        </div>

        {/* Stepper */}
        <div className="mb-8 flex items-center justify-center gap-2">
          {STEPS.map((label, i) => (
            <div key={label} className="flex items-center gap-2">
              <div className={`flex h-8 w-8 items-center justify-center rounded-full text-xs font-bold ${
                i + 1 < step ? 'bg-emerald-600 text-white' :
                i + 1 === step ? 'bg-blue-600 text-white' :
                'bg-[#1a1a2e] text-slate-500'
              }`}>
                {i + 1 < step ? <CheckCircle2 className="h-4 w-4" /> : i + 1}
              </div>
              <span className={`hidden text-xs sm:inline ${i + 1 === step ? 'text-slate-200' : 'text-slate-500'}`}>
                {label}
              </span>
              {i < STEPS.length - 1 && <ChevronRight className="h-4 w-4 text-slate-600" />}
            </div>
          ))}
        </div>

        {/* Step Content */}
        <div className="rounded-2xl border border-[#1a1a2e] bg-[#12121a] p-6">
          {step === 1 && (
            <div>
              <h2 className="mb-4 text-lg font-semibold text-slate-100">Select Ad Accounts</h2>
              <div className="mb-4 flex gap-2">
                <button onClick={selectAll} className="rounded bg-blue-600/20 px-3 py-1 text-xs text-blue-400 hover:bg-blue-600/30">Select All</button>
                <button onClick={deselectAll} className="rounded bg-slate-600/20 px-3 py-1 text-xs text-slate-400 hover:bg-slate-600/30">Deselect All</button>
              </div>
              <div className="space-y-2">
                {accounts.map((account) => (
                  <label key={account.id} className="flex cursor-pointer items-center gap-3 rounded-lg border border-[#1a1a2e] p-3 hover:bg-[#1a1a2e]/50">
                    <input
                      type="checkbox"
                      checked={selectedIds.has(account.id)}
                      onChange={() => toggleAccount(account.id)}
                      className="h-4 w-4 rounded border-slate-600 bg-transparent text-blue-600"
                    />
                    <div className="flex-1">
                      <div className="text-sm font-medium text-slate-200">{account.name}</div>
                      <div className="text-xs text-slate-500">{account.currency} · {account.timezone}</div>
                    </div>
                    {account.is_new && (
                      <span className="rounded bg-emerald-500/10 px-2 py-0.5 text-xs text-emerald-400">New</span>
                    )}
                  </label>
                ))}
                {accounts.length === 0 && (
                  <p className="py-8 text-center text-sm text-slate-500">No ad accounts found. Please connect your Facebook account first.</p>
                )}
              </div>
            </div>
          )}

          {step === 2 && (
            <div>
              <div className="mb-4 flex items-center justify-between">
                <h2 className="text-lg font-semibold text-slate-100">Set Budget Rules</h2>
                <label className="flex items-center gap-2 text-xs text-slate-400">
                  <input type="checkbox" checked={applyToAll} onChange={(e) => setApplyToAll(e.target.checked)} className="rounded" />
                  Apply to all accounts
                </label>
              </div>
              <div className="space-y-3">
                {rules.map((rule, idx) => (
                  <div key={rule.type} className="flex items-center gap-3 rounded-lg border border-[#1a1a2e] p-3">
                    <button
                      onClick={() => toggleRule(idx)}
                      className={`h-5 w-9 rounded-full transition-colors ${rule.enabled ? 'bg-blue-600' : 'bg-slate-700'}`}
                    >
                      <div className={`h-4 w-4 rounded-full bg-white transition-transform ${rule.enabled ? 'translate-x-4' : 'translate-x-0.5'}`} />
                    </button>
                    <div className="flex-1">
                      <div className="text-sm text-slate-200">{rule.label}</div>
                      <div className="text-xs text-slate-500">Action: {rule.action.replace('_', ' ')}</div>
                    </div>
                    <div className="flex items-center gap-1">
                      <span className="text-xs text-slate-500">{rule.type === 'anomaly' ? 'x' : '$'}</span>
                      <input
                        type="number"
                        value={rule.threshold}
                        onChange={(e) => updateThreshold(idx, Number(e.target.value))}
                        className="w-24 rounded border border-[#2a2a3e] bg-[#0a0a0f] px-2 py-1 text-right text-sm text-slate-200"
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {step === 3 && (
            <div>
              <h2 className="mb-4 text-lg font-semibold text-slate-100">Configure Alerts</h2>
              <div className="space-y-4">
                <div className="rounded-lg border border-[#1a1a2e] p-4">
                  <div className="mb-2 flex items-center gap-2">
                    <Bell className="h-4 w-4 text-sky-400" />
                    <span className="text-sm font-medium text-slate-200">Telegram</span>
                  </div>
                  <div className="space-y-2">
                    <input
                      placeholder="Chat ID"
                      value={alertConfig.telegramChatId}
                      onChange={(e) => setAlertConfig({ ...alertConfig, telegramChatId: e.target.value })}
                      className="w-full rounded border border-[#2a2a3e] bg-[#0a0a0f] px-3 py-2 text-sm text-slate-200 placeholder-slate-600"
                    />
                  </div>
                </div>
                <div className="rounded-lg border border-[#1a1a2e] p-4">
                  <div className="mb-2 flex items-center gap-2">
                    <Bell className="h-4 w-4 text-blue-400" />
                    <span className="text-sm font-medium text-slate-200">Email</span>
                  </div>
                  <input
                    type="email"
                    placeholder="alerts@example.com"
                    value={alertConfig.email}
                    onChange={(e) => setAlertConfig({ ...alertConfig, email: e.target.value })}
                    className="w-full rounded border border-[#2a2a3e] bg-[#0a0a0f] px-3 py-2 text-sm text-slate-200 placeholder-slate-600"
                  />
                </div>
                <div className="rounded-lg border border-[#1a1a2e] p-4 opacity-60">
                  <div className="flex items-center gap-2">
                    <input type="checkbox" checked disabled className="rounded" />
                    <span className="text-sm text-slate-400">In-App Notifications (always enabled)</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {step === 4 && (
            <div>
              <h2 className="mb-4 text-lg font-semibold text-slate-100">Review & Activate</h2>
              <div className="grid grid-cols-3 gap-4 mb-6">
                <div className="rounded-lg bg-[#0a0a0f] p-4 text-center">
                  <div className="text-2xl font-bold text-blue-400">{selectedIds.size}</div>
                  <div className="text-xs text-slate-500">Accounts</div>
                </div>
                <div className="rounded-lg bg-[#0a0a0f] p-4 text-center">
                  <div className="text-2xl font-bold text-purple-400">{rules.filter((r) => r.enabled).length * selectedIds.size}</div>
                  <div className="text-xs text-slate-500">Rules</div>
                </div>
                <div className="rounded-lg bg-[#0a0a0f] p-4 text-center">
                  <div className="text-2xl font-bold text-emerald-400">
                    {[alertConfig.telegramChatId, alertConfig.email, 'in-app'].filter(Boolean).length}
                  </div>
                  <div className="text-xs text-slate-500">Alert Channels</div>
                </div>
              </div>
              <button
                onClick={handleActivate}
                disabled={activating}
                className="flex w-full items-center justify-center gap-2 rounded-xl bg-emerald-600 px-6 py-3 text-sm font-semibold text-white hover:bg-emerald-700 disabled:opacity-50"
              >
                {activating ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Rocket className="h-4 w-4" />
                )}
                {activating ? 'Activating...' : 'Start Monitoring'}
              </button>
            </div>
          )}
        </div>

        {/* Navigation */}
        <div className="mt-6 flex justify-between">
          <button
            onClick={() => step > 1 ? setStep(step - 1) : navigate('/settings')}
            className="flex items-center gap-1 text-sm text-slate-400 hover:text-slate-200"
          >
            <ChevronLeft className="h-4 w-4" />
            {step > 1 ? 'Back' : 'Settings'}
          </button>
          {step < 4 && (
            <button
              onClick={() => setStep(step + 1)}
              disabled={step === 1 && selectedIds.size === 0}
              className="flex items-center gap-1 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              Next
              <ChevronRight className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
