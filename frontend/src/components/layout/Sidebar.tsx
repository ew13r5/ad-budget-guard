import { NavLink } from 'react-router-dom'
import { useUIStore } from '@/stores/uiStore'
import {
  LayoutDashboard,
  Users,
  ShieldCheck,
  FlaskConical,
  Activity,
  Settings,
  ChevronLeft,
  ChevronRight,
  Shield,
} from 'lucide-react'

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard', end: true },
  { to: '/accounts', icon: Users, label: 'Accounts', end: false },
  { to: '/rules', icon: ShieldCheck, label: 'Rules', end: false },
  { to: '/simulation', icon: FlaskConical, label: 'Simulation', end: false },
  { to: '/activity', icon: Activity, label: 'Activity', end: false },
  { to: '/settings', icon: Settings, label: 'Settings', end: false },
]

export function Sidebar() {
  const { sidebarOpen, toggleSidebar } = useUIStore()

  return (
    <aside
      className={`flex h-screen flex-col border-r border-[#1a1a2e] bg-[#0c0c14] transition-all duration-200 ${
        sidebarOpen ? 'w-60' : 'w-16'
      }`}
    >
      {/* Logo */}
      <div className="flex h-16 items-center gap-3 border-b border-[#1a1a2e] px-4">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-blue-600">
          <Shield className="h-4 w-4 text-white" />
        </div>
        {sidebarOpen && (
          <span className="text-sm font-bold tracking-tight text-slate-100">
            Ad Budget Guard
          </span>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 p-3">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-blue-600/10 text-blue-400'
                  : 'text-slate-400 hover:bg-[#1a1a2e] hover:text-slate-200'
              }`
            }
          >
            <item.icon className="h-4.5 w-4.5 shrink-0" />
            {sidebarOpen && <span>{item.label}</span>}
          </NavLink>
        ))}
      </nav>

      {/* Collapse toggle */}
      <div className="border-t border-[#1a1a2e] p-3">
        <button
          onClick={toggleSidebar}
          className="flex w-full items-center justify-center rounded-lg py-2 text-slate-500 transition-colors hover:bg-[#1a1a2e] hover:text-slate-300"
        >
          {sidebarOpen ? <ChevronLeft className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
        </button>
      </div>
    </aside>
  )
}
