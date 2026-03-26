import { EmptyState } from '@/components/common/EmptyState'
import { AccountMode } from '@/api/types'
import {
  Settings,
  Moon,
  Bell,
  Shield,
} from 'lucide-react'

const mockAccounts = [
  { id: 'acc-alpha', name: 'Client-Alpha', metaId: 'act_123456789', mode: AccountMode.simulation },
  { id: 'acc-beta', name: 'Client-Beta', metaId: 'act_987654321', mode: AccountMode.sandbox },
  { id: 'acc-gamma', name: 'Client-Gamma', metaId: 'act_456789123', mode: AccountMode.production },
  { id: 'acc-delta', name: 'Client-Delta', metaId: 'act_789123456', mode: AccountMode.production },
  { id: 'acc-epsilon', name: 'Client-Epsilon', metaId: 'act_321654987', mode: AccountMode.sandbox },
]

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="rounded-lg bg-slate-500/10 p-2">
          <Settings className="h-5 w-5 text-slate-400" />
        </div>
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-100">Settings</h1>
          <p className="text-sm text-slate-500">Configure account modes and preferences</p>
        </div>
      </div>

      {/* Account Modes */}
      <div className="rounded-xl border border-[#1a1a2e] bg-[#12121a] p-6">
        <div className="mb-4 flex items-center gap-2">
          <Shield className="h-4 w-4 text-blue-400" />
          <h2 className="text-sm font-semibold text-slate-200">Account Modes</h2>
        </div>
        <p className="mb-4 text-xs text-slate-500">
          Switch accounts between Sandbox, Simulation, and Production modes.
        </p>
        <div className="space-y-3">
          {mockAccounts.map((account) => (
            <div
              key={account.id}
              className="flex items-center justify-between rounded-lg border border-[#1a1a2e] px-4 py-3"
            >
              <div>
                <p className="text-sm font-medium text-slate-200">{account.name}</p>
                <p className="font-mono text-xs text-slate-500">{account.metaId}</p>
              </div>
              <select
                defaultValue={account.mode}
                onChange={(e) => {
                  if (e.target.value === 'production') {
                    if (!window.confirm('Switch to Production mode? This will connect to real Meta Ads data.')) {
                      e.target.value = account.mode
                    }
                  }
                }}
                className="rounded-lg border border-[#2a2a3e] bg-[#0a0a0f] px-3 py-1.5 text-xs font-medium text-slate-300 focus:border-blue-500 focus:outline-none"
              >
                <option value="sandbox">Sandbox</option>
                <option value="simulation">Simulation</option>
                <option value="production">Production</option>
              </select>
            </div>
          ))}
        </div>
      </div>

      {/* Appearance */}
      <div className="rounded-xl border border-[#1a1a2e] bg-[#12121a] p-6">
        <div className="mb-4 flex items-center gap-2">
          <Moon className="h-4 w-4 text-purple-400" />
          <h2 className="text-sm font-semibold text-slate-200">Appearance</h2>
        </div>
        <div className="flex items-center justify-between rounded-lg border border-[#1a1a2e] px-4 py-3">
          <div>
            <p className="text-sm font-medium text-slate-200">Dark Mode</p>
            <p className="text-xs text-slate-500">Always-on dark theme for reduced eye strain</p>
          </div>
          <div className="flex items-center gap-2 rounded-lg bg-emerald-500/10 px-3 py-1.5 text-xs font-medium text-emerald-400">
            <div className="h-2 w-2 rounded-full bg-emerald-500" />
            Always On
          </div>
        </div>
      </div>

      {/* Alert Notifications */}
      <div className="rounded-xl border border-[#1a1a2e] bg-[#12121a] p-6">
        <div className="mb-4 flex items-center gap-2">
          <Bell className="h-4 w-4 text-amber-400" />
          <h2 className="text-sm font-semibold text-slate-200">Alert Notifications</h2>
        </div>
        <EmptyState
          icon={<Bell className="h-10 w-10" />}
          title="Coming Soon"
          description="Alert configuration (Telegram, email, Slack) will be available in a future update."
        />
      </div>
    </div>
  )
}
