import { useEffect, useState, type ReactNode } from 'react'
import { useAuthStore } from '@/stores/authStore'
import { devLogin, fetchMe } from '@/api/auth'
import { Loader2 } from 'lucide-react'

export function AuthGuard({ children }: { children: ReactNode }) {
  const [ready, setReady] = useState(false)
  const { setTokens, setUser, accessToken } = useAuthStore()

  useEffect(() => {
    async function init() {
      // If we have an existing token, try to validate it
      if (accessToken) {
        try {
          const user = await fetchMe()
          setUser(user)
          setReady(true)
          return
        } catch {
          // Token is invalid, fall through to dev-login
        }
      }

      // Try dev-login for development
      try {
        const tokens = await devLogin()
        setTokens(tokens)
        const user = await fetchMe()
        setUser(user)
      } catch {
        // No backend available — bypass auth for portfolio display
        setUser({
          id: 'demo-user',
          name: 'Demo User',
          email: 'demo@adbudgetguard.com',
          needs_reauth: false,
        })
      }
      setReady(true)
    }

    init()
  }, [accessToken, setTokens, setUser])

  if (!ready) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-[#0a0a0f]">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
          <p className="text-sm text-slate-400">Initializing Ad Budget Guard...</p>
        </div>
      </div>
    )
  }

  return <>{children}</>
}
