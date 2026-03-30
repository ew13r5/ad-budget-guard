import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ConnectionStatus } from '@/components/common/ConnectionStatus'
import { ModeIndicator } from '@/components/common/ModeIndicator'
import { AccountMode } from '@/api/types'
import { useAuthStore } from '@/stores/authStore'
import { facebookLogin } from '@/api/auth'
import { Bell, User, AlertTriangle } from 'lucide-react'

export function Header() {
  const navigate = useNavigate()
  const user = useAuthStore((s) => s.user)
  const [reconnecting, setReconnecting] = useState(false)

  const handleReconnect = async () => {
    setReconnecting(true)
    try {
      const { auth_url } = await facebookLogin()
      window.location.href = auth_url
    } catch {
      setReconnecting(false)
    }
  }

  return (
    <>
      {user?.needs_reauth && (
        <div className="flex items-center justify-center gap-2 border-b border-amber-500/20 bg-amber-500/10 px-4 py-2 text-sm">
          <AlertTriangle className="h-4 w-4 text-amber-400" />
          <span className="text-amber-300">Your Facebook connection has expired.</span>
          <button
            onClick={handleReconnect}
            disabled={reconnecting}
            className="ml-2 rounded bg-amber-600 px-3 py-0.5 text-xs font-medium text-white hover:bg-amber-700 disabled:opacity-50"
          >
            {reconnecting ? 'Connecting...' : 'Reconnect'}
          </button>
        </div>
      )}
      <header className="flex h-14 items-center justify-between border-b border-[#1a1a2e] bg-[#0c0c14]/80 px-6 backdrop-blur-sm">
        <div className="flex items-center gap-4">
          <ModeIndicator mode={AccountMode.simulation} />
          <ConnectionStatus />
        </div>

        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/notifications')}
            className="relative rounded-lg p-2 text-slate-400 transition-colors hover:bg-[#1a1a2e] hover:text-slate-200"
          >
            <Bell className="h-4.5 w-4.5" />
            <span className="absolute -right-0.5 -top-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[10px] font-bold text-white">
              3
            </span>
          </button>

          <div className="flex items-center gap-2 rounded-lg px-3 py-1.5 text-sm text-slate-300">
            <div className="flex h-7 w-7 items-center justify-center rounded-full bg-blue-600/20">
              <User className="h-3.5 w-3.5 text-blue-400" />
            </div>
            <span className="text-sm font-medium">{user?.name || 'Demo User'}</span>
          </div>
        </div>
      </header>
    </>
  )
}
