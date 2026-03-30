import { useEffect, useState } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { facebookAuth, fetchMe } from '@/api/auth'
import { useAuthStore } from '@/stores/authStore'
import { Loader2, AlertCircle, CheckCircle2 } from 'lucide-react'

export default function AuthCallbackPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const { setTokens, setUser } = useAuthStore()
  const [status, setStatus] = useState<'loading' | 'error' | 'success'>('loading')
  const [errorMessage, setErrorMessage] = useState('')

  useEffect(() => {
    const code = searchParams.get('code')
    const state = searchParams.get('state')
    const error = searchParams.get('error')
    const errorDesc = searchParams.get('error_description')

    if (error) {
      setStatus('error')
      setErrorMessage(errorDesc || 'Facebook authorization was denied.')
      return
    }

    if (!code) {
      setStatus('error')
      setErrorMessage('No authorization code received.')
      return
    }

    async function exchangeCode() {
      try {
        const tokens = await facebookAuth(code!, state || undefined)
        setTokens(tokens)
        const user = await fetchMe()
        setUser(user)
        setStatus('success')
        setTimeout(() => navigate('/'), 500)
      } catch (err: any) {
        setStatus('error')
        setErrorMessage(err?.response?.data?.detail || 'Failed to connect Facebook account.')
      }
    }

    exchangeCode()
  }, [searchParams, navigate, setTokens, setUser])

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#0a0a12]">
      <div className="w-full max-w-md rounded-2xl border border-[#1a1a2e] bg-[#12121a] p-8 text-center">
        {status === 'loading' && (
          <>
            <Loader2 className="mx-auto h-12 w-12 animate-spin text-blue-400" />
            <h2 className="mt-4 text-lg font-semibold text-slate-100">
              Connecting your Facebook account...
            </h2>
            <p className="mt-2 text-sm text-slate-500">
              Please wait while we complete the authorization.
            </p>
          </>
        )}

        {status === 'success' && (
          <>
            <CheckCircle2 className="mx-auto h-12 w-12 text-emerald-400" />
            <h2 className="mt-4 text-lg font-semibold text-slate-100">
              Connected!
            </h2>
            <p className="mt-2 text-sm text-slate-500">
              Redirecting to dashboard...
            </p>
          </>
        )}

        {status === 'error' && (
          <>
            <AlertCircle className="mx-auto h-12 w-12 text-red-400" />
            <h2 className="mt-4 text-lg font-semibold text-slate-100">
              Connection Failed
            </h2>
            <p className="mt-2 text-sm text-red-400/80">
              {errorMessage}
            </p>
            <div className="mt-6 flex flex-col gap-2">
              <button
                onClick={() => navigate('/settings')}
                className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
              >
                Try Again
              </button>
              <button
                onClick={() => navigate('/')}
                className="text-sm text-slate-500 hover:text-slate-400"
              >
                Back to Dashboard
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
