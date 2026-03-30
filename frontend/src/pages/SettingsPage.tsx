import { useState, useEffect } from 'react'
import { AccountMode } from '@/api/types'
import {
  Settings,
  Moon,
  Bell,
  Shield,
  Key,
  MessageCircle,
  Mail,
  Eye,
  EyeOff,
  Send,
} from 'lucide-react'
import { toast } from 'sonner'
import { useAuthStore } from '@/stores/authStore'
import { facebookLogin } from '@/api/auth'

const mockAccounts = [
  { id: 'acc-alpha', name: 'Client-Alpha', metaId: 'act_123456789', mode: AccountMode.simulation },
  { id: 'acc-beta', name: 'Client-Beta', metaId: 'act_987654321', mode: AccountMode.sandbox },
  { id: 'acc-gamma', name: 'Client-Gamma', metaId: 'act_456789123', mode: AccountMode.production },
  { id: 'acc-delta', name: 'Client-Delta', metaId: 'act_789123456', mode: AccountMode.production },
  { id: 'acc-epsilon', name: 'Client-Epsilon', metaId: 'act_321654987', mode: AccountMode.sandbox },
]

function MaskedInput({
  label,
  value,
  placeholder,
}: {
  label: string
  value: string
  placeholder: string
}) {
  const [visible, setVisible] = useState(false)
  const [inputValue, setInputValue] = useState(value)

  return (
    <div>
      <label className="mb-1.5 block text-xs font-medium text-slate-400">{label}</label>
      <div className="relative">
        <input
          type={visible ? 'text' : 'password'}
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          placeholder={placeholder}
          className="w-full rounded-lg border border-[#2a2a3e] bg-[#0a0a0f] px-3 py-2 pr-10 font-mono text-xs text-slate-300 placeholder-slate-600 focus:border-blue-500 focus:outline-none"
        />
        <button
          type="button"
          onClick={() => setVisible(!visible)}
          className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300"
        >
          {visible ? <EyeOff className="h-3.5 w-3.5" /> : <Eye className="h-3.5 w-3.5" />}
        </button>
      </div>
    </div>
  )
}

export default function SettingsPage() {
  useEffect(() => { document.title = 'Settings | Ad Budget Guard' }, [])
  const [inAppEnabled, setInAppEnabled] = useState(true)
  const [connectingFb, setConnectingFb] = useState(false)
  const user = useAuthStore((s) => s.user)

  function handleTestConnection(service: string) {
    toast.success(`${service} connection test successful (demo)`)
  }

  async function handleConnectFacebook() {
    setConnectingFb(true)
    try {
      const { auth_url } = await facebookLogin()
      window.location.href = auth_url
    } catch {
      toast.error('Failed to start Facebook connection')
      setConnectingFb(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="rounded-lg bg-slate-500/10 p-2">
          <Settings className="h-5 w-5 text-slate-400" />
        </div>
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-100">Settings</h1>
          <p className="text-sm text-slate-500">Configure account modes, integrations, and notifications</p>
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

      {/* Meta API Configuration */}
      <div className="rounded-xl border border-[#1a1a2e] bg-[#12121a] p-6">
        <div className="mb-4 flex items-center gap-2">
          <Key className="h-4 w-4 text-blue-400" />
          <h2 className="text-sm font-semibold text-slate-200">Meta API Configuration</h2>
        </div>
        <p className="mb-4 text-xs text-slate-500">
          Connect to Meta Business API for live ad account data.
        </p>
        <div className="space-y-4">
          {user?.needs_reauth ? (
            <div className="flex items-center gap-3">
              <span className="flex items-center gap-1.5 text-xs text-amber-400">
                <div className="h-1.5 w-1.5 rounded-full bg-amber-500" />
                Reconnection required
              </span>
              <button
                onClick={handleConnectFacebook}
                disabled={connectingFb}
                className="inline-flex items-center gap-2 rounded-lg bg-[#1877F2] px-4 py-2 text-xs font-medium text-white transition-colors hover:bg-[#1565C0] disabled:opacity-50"
              >
                {connectingFb ? 'Connecting...' : 'Reconnect Facebook'}
              </button>
            </div>
          ) : user?.name && user.name !== 'Demo User' ? (
            <div className="flex items-center gap-3">
              <span className="flex items-center gap-1.5 text-xs text-emerald-400">
                <div className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                Connected as {user.name}
              </span>
              <button
                onClick={handleConnectFacebook}
                disabled={connectingFb}
                className="inline-flex items-center gap-2 rounded-lg border border-[#2a2a3e] px-3 py-1.5 text-xs font-medium text-slate-400 transition-colors hover:bg-[#1a1a2e] hover:text-slate-200 disabled:opacity-50"
              >
                Reconnect
              </button>
            </div>
          ) : (
            <button
              onClick={handleConnectFacebook}
              disabled={connectingFb}
              className="inline-flex items-center gap-2 rounded-lg bg-[#1877F2] px-5 py-2.5 text-sm font-medium text-white transition-colors hover:bg-[#1565C0] disabled:opacity-50"
            >
              {connectingFb ? 'Connecting...' : 'Connect Facebook Account'}
            </button>
          )}
        </div>
      </div>

      {/* Telegram Configuration */}
      <div className="rounded-xl border border-[#1a1a2e] bg-[#12121a] p-6">
        <div className="mb-4 flex items-center gap-2">
          <MessageCircle className="h-4 w-4 text-sky-400" />
          <h2 className="text-sm font-semibold text-slate-200">Telegram Notifications</h2>
        </div>
        <p className="mb-4 text-xs text-slate-500">
          Receive real-time budget alerts via Telegram bot.
        </p>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <MaskedInput
            label="Bot Token"
            value="7123456789:AAHfG..."
            placeholder="Enter Telegram bot token"
          />
          <MaskedInput
            label="Chat ID"
            value="-1001234567890"
            placeholder="Enter Telegram chat ID"
          />
        </div>
        <div className="mt-4 flex items-center gap-3">
          <button
            onClick={() => handleTestConnection('Telegram')}
            className="inline-flex items-center gap-2 rounded-lg bg-sky-600 px-4 py-2 text-xs font-medium text-white transition-colors hover:bg-sky-700"
          >
            <Send className="h-3.5 w-3.5" />
            Send Test Message
          </button>
        </div>
      </div>

      {/* Email Configuration */}
      <div className="rounded-xl border border-[#1a1a2e] bg-[#12121a] p-6">
        <div className="mb-4 flex items-center gap-2">
          <Mail className="h-4 w-4 text-purple-400" />
          <h2 className="text-sm font-semibold text-slate-200">Email Notifications</h2>
        </div>
        <p className="mb-4 text-xs text-slate-500">
          Configure SMTP settings for email alert delivery.
        </p>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className="mb-1.5 block text-xs font-medium text-slate-400">SMTP Host</label>
            <input
              type="text"
              defaultValue="smtp.gmail.com"
              className="w-full rounded-lg border border-[#2a2a3e] bg-[#0a0a0f] px-3 py-2 font-mono text-xs text-slate-300 placeholder-slate-600 focus:border-blue-500 focus:outline-none"
            />
          </div>
          <div>
            <label className="mb-1.5 block text-xs font-medium text-slate-400">SMTP Port</label>
            <input
              type="text"
              defaultValue="587"
              className="w-full rounded-lg border border-[#2a2a3e] bg-[#0a0a0f] px-3 py-2 font-mono text-xs text-slate-300 placeholder-slate-600 focus:border-blue-500 focus:outline-none"
            />
          </div>
          <div>
            <label className="mb-1.5 block text-xs font-medium text-slate-400">From Address</label>
            <input
              type="email"
              defaultValue="alerts@adbudgetguard.com"
              className="w-full rounded-lg border border-[#2a2a3e] bg-[#0a0a0f] px-3 py-2 font-mono text-xs text-slate-300 placeholder-slate-600 focus:border-blue-500 focus:outline-none"
            />
          </div>
          <MaskedInput
            label="SMTP Password"
            value="xyzp-abcd-efgh-ijkl"
            placeholder="Enter SMTP password"
          />
        </div>
        <div className="mt-4 flex items-center gap-3">
          <button
            onClick={() => handleTestConnection('Email')}
            className="inline-flex items-center gap-2 rounded-lg bg-purple-600 px-4 py-2 text-xs font-medium text-white transition-colors hover:bg-purple-700"
          >
            <Send className="h-3.5 w-3.5" />
            Send Test Email
          </button>
        </div>
      </div>

      {/* In-App Notifications */}
      <div className="rounded-xl border border-[#1a1a2e] bg-[#12121a] p-6">
        <div className="mb-4 flex items-center gap-2">
          <Bell className="h-4 w-4 text-amber-400" />
          <h2 className="text-sm font-semibold text-slate-200">In-App Notifications</h2>
        </div>
        <div className="flex items-center justify-between rounded-lg border border-[#1a1a2e] px-4 py-3">
          <div>
            <p className="text-sm font-medium text-slate-200">Toast Notifications</p>
            <p className="text-xs text-slate-500">Show real-time alerts as in-app toast messages</p>
          </div>
          <button
            onClick={() => setInAppEnabled(!inAppEnabled)}
            className="relative inline-flex h-6 w-11 shrink-0 cursor-pointer items-center rounded-full transition-colors duration-200 focus:outline-none"
            style={{ backgroundColor: inAppEnabled ? '#10b981' : '#334155' }}
            role="switch"
            aria-checked={inAppEnabled}
          >
            <span
              className="inline-block h-4 w-4 rounded-full bg-white shadow transition-transform duration-200"
              style={{ transform: inAppEnabled ? 'translateX(22px)' : 'translateX(4px)' }}
            />
          </button>
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
    </div>
  )
}
