import { lazy, Suspense } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryProvider } from '@/providers/QueryProvider'
import { AuthGuard } from '@/providers/AuthGuard'
import { WebSocketProvider } from '@/providers/WebSocketProvider'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { Toaster } from 'sonner'

const DashboardPage = lazy(() => import('@/pages/DashboardPage'))
const AccountsPage = lazy(() => import('@/pages/AccountsPage'))
const AccountDetailPage = lazy(() => import('@/pages/AccountDetailPage'))
const RulesPage = lazy(() => import('@/pages/RulesPage'))
const SimulationPage = lazy(() => import('@/pages/SimulationPage'))
const ActivityPage = lazy(() => import('@/pages/ActivityPage'))
const NotificationsPage = lazy(() => import('@/pages/NotificationsPage'))
const SettingsPage = lazy(() => import('@/pages/SettingsPage'))
const AuthCallbackPage = lazy(() => import('@/pages/AuthCallbackPage'))
const OnboardingPage = lazy(() => import('@/pages/OnboardingPage'))

export default function App() {
  return (
    <QueryProvider>
      <AuthGuard>
        <WebSocketProvider>
          <BrowserRouter>
            <Routes>
              <Route
                path="auth/callback"
                element={
                  <Suspense fallback={<LoadingSpinner />}>
                    <AuthCallbackPage />
                  </Suspense>
                }
              />
              <Route
                path="onboarding"
                element={
                  <Suspense fallback={<LoadingSpinner />}>
                    <OnboardingPage />
                  </Suspense>
                }
              />
              <Route element={<DashboardLayout />}>
                <Route
                  index
                  element={
                    <Suspense fallback={<LoadingSpinner />}>
                      <DashboardPage />
                    </Suspense>
                  }
                />
                <Route
                  path="accounts"
                  element={
                    <Suspense fallback={<LoadingSpinner />}>
                      <AccountsPage />
                    </Suspense>
                  }
                />
                <Route
                  path="accounts/:id"
                  element={
                    <Suspense fallback={<LoadingSpinner />}>
                      <AccountDetailPage />
                    </Suspense>
                  }
                />
                <Route
                  path="rules"
                  element={
                    <Suspense fallback={<LoadingSpinner />}>
                      <RulesPage />
                    </Suspense>
                  }
                />
                <Route
                  path="simulation"
                  element={
                    <Suspense fallback={<LoadingSpinner />}>
                      <SimulationPage />
                    </Suspense>
                  }
                />
                <Route
                  path="activity"
                  element={
                    <Suspense fallback={<LoadingSpinner />}>
                      <ActivityPage />
                    </Suspense>
                  }
                />
                <Route
                  path="notifications"
                  element={
                    <Suspense fallback={<LoadingSpinner />}>
                      <NotificationsPage />
                    </Suspense>
                  }
                />
                <Route
                  path="settings"
                  element={
                    <Suspense fallback={<LoadingSpinner />}>
                      <SettingsPage />
                    </Suspense>
                  }
                />
                <Route path="*" element={<Navigate to="/" replace />} />
              </Route>
            </Routes>
          </BrowserRouter>
          <Toaster
            position="top-right"
            theme="dark"
            toastOptions={{
              style: {
                background: '#1a1a2e',
                border: '1px solid #2a2a3e',
                color: '#e2e8f0',
              },
            }}
          />
        </WebSocketProvider>
      </AuthGuard>
    </QueryProvider>
  )
}
