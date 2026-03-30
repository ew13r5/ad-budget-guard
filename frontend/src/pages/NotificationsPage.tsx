import { Check, AlertTriangle, ShieldAlert, Info, Filter, Inbox } from 'lucide-react'
import { useState, useEffect } from 'react'
import { EmptyState } from '@/components/common/EmptyState'

type NotificationType = 'all' | 'anomaly' | 'pause' | 'warning' | 'info'

const mockNotifications = [
  {
    id: '1',
    type: 'anomaly' as const,
    title: 'Anomaly Detected',
    message: 'Client-Delta — spend spike 847% above 15-min average. All 6 campaigns hard-paused.',
    account: 'Client-Delta — Restaurant Chain',
    time: '14:32:01',
    date: 'Today',
    read: false,
  },
  {
    id: '2',
    type: 'pause' as const,
    title: 'Campaigns Paused',
    message: 'Client-Gamma — 3 campaigns exceeded daily budget. Soft pause applied.',
    account: 'Client-Gamma — Real Estate Agency',
    time: '14:22:03',
    date: 'Today',
    read: false,
  },
  {
    id: '3',
    type: 'warning' as const,
    title: 'Budget Warning (80%)',
    message: 'Client-Alpha — spend at 87.1% of daily budget ($174.20 / $200.00). Forecast: $241.50 by EOD.',
    account: 'Client-Alpha — E-commerce Brand',
    time: '13:15:22',
    date: 'Today',
    read: false,
  },
  {
    id: '4',
    type: 'info' as const,
    title: 'Daily Report Generated',
    message: 'Daily spend report for all accounts has been generated and is ready for download.',
    account: 'System',
    time: '08:00:01',
    date: 'Today',
    read: true,
  },
  {
    id: '5',
    type: 'pause' as const,
    title: 'Auto-Resume Complete',
    message: '5 campaigns auto-resumed after daily budget reset.',
    account: 'Multiple accounts',
    time: '00:05:12',
    date: 'Today',
    read: true,
  },
  {
    id: '6',
    type: 'anomaly' as const,
    title: 'Anomaly Detected',
    message: 'Client-Delta — unusual spend pattern detected. Spend rate 4.2x above average.',
    account: 'Client-Delta — Restaurant Chain',
    time: '22:15:44',
    date: 'Yesterday',
    read: true,
  },
  {
    id: '7',
    type: 'warning' as const,
    title: 'Monthly Budget Warning (90%)',
    message: 'Client-Alpha — monthly spend at 92% ($4,600 / $5,000).',
    account: 'Client-Alpha — E-commerce Brand',
    time: '18:00:00',
    date: 'Yesterday',
    read: true,
  },
]

const typeConfig = {
  anomaly: { icon: ShieldAlert, color: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/30' },
  pause: { icon: AlertTriangle, color: 'text-amber-400', bg: 'bg-amber-500/10', border: 'border-amber-500/30' },
  warning: { icon: AlertTriangle, color: 'text-yellow-400', bg: 'bg-yellow-500/10', border: 'border-yellow-500/30' },
  info: { icon: Info, color: 'text-blue-400', bg: 'bg-blue-500/10', border: 'border-blue-500/30' },
}

export default function NotificationsPage() {
  const [filter, setFilter] = useState<NotificationType>('all')
  const [notifications, setNotifications] = useState(mockNotifications)

  const filtered = filter === 'all'
    ? notifications
    : notifications.filter((n) => n.type === filter)

  const unreadCount = notifications.filter((n) => !n.read).length

  function markAllRead() {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })))
  }

  function markRead(id: string) {
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, read: true } : n))
    )
  }

  useEffect(() => { document.title = 'Notifications | Ad Budget Guard' }, [])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold text-slate-100">Notifications</h1>
          {unreadCount > 0 && (
            <span className="rounded-full bg-red-500 px-2.5 py-0.5 text-xs font-medium text-white">
              {unreadCount} unread
            </span>
          )}
        </div>
        {unreadCount > 0 && (
          <button
            onClick={markAllRead}
            className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium text-slate-400 transition-colors hover:bg-[#1a1a2e] hover:text-slate-200"
          >
            <Check className="h-3.5 w-3.5" />
            Mark all read
          </button>
        )}
      </div>

      {/* Filters */}
      <div className="flex items-center gap-2">
        <Filter className="h-4 w-4 text-slate-500" />
        {(['all', 'anomaly', 'pause', 'warning', 'info'] as NotificationType[]).map((t) => (
          <button
            key={t}
            onClick={() => setFilter(t)}
            className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
              filter === t
                ? 'bg-blue-600/20 text-blue-400'
                : 'text-slate-400 hover:bg-[#1a1a2e] hover:text-slate-200'
            }`}
          >
            {t === 'all' ? 'All' : t.charAt(0).toUpperCase() + t.slice(1)}
          </button>
        ))}
      </div>

      {/* Notification list */}
      <div className="space-y-2">
        {filtered.length === 0 && (
          <EmptyState
            icon={<Inbox className="h-10 w-10" />}
            title="No notifications"
            description="No notifications match the selected filter."
          />
        )}
        {filtered.map((notif) => {
          const config = typeConfig[notif.type]
          const Icon = config.icon
          return (
            <div
              key={notif.id}
              onClick={() => markRead(notif.id)}
              className={`flex gap-4 rounded-xl border p-4 transition-colors cursor-pointer ${
                notif.read
                  ? 'border-[#1a1a2e] bg-[#12121a]'
                  : `${config.border} ${config.bg}`
              }`}
            >
              <div className={`mt-0.5 shrink-0 ${config.color}`}>
                <Icon className="h-5 w-5" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <p className={`text-sm font-medium ${notif.read ? 'text-slate-300' : 'text-slate-100'}`}>
                      {notif.title}
                    </p>
                    <p className="text-xs text-slate-500 mt-0.5">{notif.account}</p>
                  </div>
                  <div className="text-right shrink-0">
                    <p className="text-xs text-slate-500">{notif.time}</p>
                    <p className="text-xs text-slate-600">{notif.date}</p>
                  </div>
                </div>
                <p className="text-sm text-slate-400 mt-1.5">{notif.message}</p>
              </div>
              {!notif.read && (
                <div className="shrink-0 mt-2">
                  <div className="h-2 w-2 rounded-full bg-blue-500" />
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
