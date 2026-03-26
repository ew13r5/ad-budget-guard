import { ChevronDown } from 'lucide-react'

interface ScenarioDropdownProps {
  currentScenario: string
  onScenarioChange: (scenario: string) => void
  disabled?: boolean
}

const scenarios = [
  { value: 'normal', label: 'Normal Spending' },
  { value: 'approaching_limit', label: 'Approaching Limit' },
  { value: 'budget_exceeded', label: 'Budget Exceeded' },
  { value: 'hack_simulation', label: 'Hack Simulation' },
]

export function ScenarioDropdown({ currentScenario, onScenarioChange, disabled }: ScenarioDropdownProps) {
  return (
    <div className="relative">
      <select
        value={currentScenario}
        onChange={(e) => onScenarioChange(e.target.value)}
        disabled={disabled}
        className="appearance-none rounded-lg border border-[#2a2a3e] bg-[#0a0a0f] py-2 pl-3 pr-8 text-xs font-medium text-slate-300 transition-colors hover:border-[#3a3a4e] focus:border-blue-500 focus:outline-none disabled:opacity-50"
      >
        {scenarios.map((s) => (
          <option key={s.value} value={s.value}>
            {s.label}
          </option>
        ))}
      </select>
      <ChevronDown className="pointer-events-none absolute right-2 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-slate-500" />
    </div>
  )
}
