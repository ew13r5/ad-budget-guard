import { useState, useCallback } from 'react'
import { SpeedSelector } from '@/components/simulation/SpeedSelector'
import { ScenarioDropdown } from '@/components/simulation/ScenarioDropdown'
import { SimulationLog } from '@/components/simulation/SimulationLog'
import { StatusBadge } from '@/components/common/StatusBadge'
import {
  startSimulation,
  pauseSimulation,
  setSpeed as apiSetSpeed,
  setScenario as apiSetScenario,
  triggerAnomaly as apiTriggerAnomaly,
  resetSimulation as apiResetSimulation,
} from '@/api/simulation'
import { toast } from 'sonner'
import {
  Play,
  Pause,
  Zap,
  RotateCcw,
  Clock,
  Hash,
  Monitor,
  FlaskConical,
} from 'lucide-react'

// Demo state
const initialLogEntries = [
  { id: '1', time: '14:23:01', type: 'tick', message: 'Simulation tick #142 processed' },
  { id: '2', time: '14:23:05', type: 'anomaly', message: 'Anomaly detected: spend rate 3.2x above normal for campaign "Summer Sale - Broad"', campaignId: 'c1' },
  { id: '3', time: '14:23:05', type: 'pause', message: 'Campaign "Summer Sale - Broad" auto-paused by rule "Daily Limit Guard"', campaignId: 'c1' },
  { id: '4', time: '14:23:10', type: 'tick', message: 'Simulation tick #143 processed' },
  { id: '5', time: '14:23:15', type: 'anomaly', message: 'Budget threshold 95% reached for "Product Catalog - DPA"', campaignId: 'c5' },
  { id: '6', time: '14:23:15', type: 'pause', message: 'Campaign "Product Catalog - DPA" paused - soft limit exceeded', campaignId: 'c5' },
  { id: '7', time: '14:23:20', type: 'tick', message: 'Simulation tick #144 processed' },
  { id: '8', time: '14:23:25', type: 'trigger', message: 'Manual anomaly triggered on "Competitor Targeting"', campaignId: 'c10' },
]

export default function SimulationPage() {
  const [simStatus, setSimStatus] = useState<'running' | 'paused' | 'stopped'>('paused')
  const [speed, setSpeed] = useState<1 | 2 | 5 | 10>(1)
  const [scenario, setScenario] = useState('normal')
  const [tickCount, setTickCount] = useState(144)
  const [logEntries, setLogEntries] = useState(initialLogEntries)
  const [isLoading, setIsLoading] = useState(false)

  const addLogEntry = useCallback((type: string, message: string) => {
    const now = new Date()
    const time = now.toLocaleTimeString('en-US', { hour12: false })
    setLogEntries((prev) => [
      ...prev,
      { id: Date.now().toString(), time, type, message },
    ])
  }, [])

  const handleStartPause = useCallback(async () => {
    setIsLoading(true)
    try {
      if (simStatus === 'running') {
        await pauseSimulation()
        setSimStatus('paused')
        addLogEntry('pause', 'Simulation paused')
        toast.success('Simulation paused')
      } else {
        await startSimulation(scenario)
        setSimStatus('running')
        addLogEntry('resume', 'Simulation started')
        toast.success('Simulation started')
      }
    } catch {
      // Demo mode fallback
      if (simStatus === 'running') {
        setSimStatus('paused')
        addLogEntry('pause', 'Simulation paused (demo mode)')
      } else {
        setSimStatus('running')
        addLogEntry('resume', 'Simulation started (demo mode)')
      }
    } finally {
      setIsLoading(false)
    }
  }, [simStatus, scenario, addLogEntry])

  const handleSpeedChange = useCallback(async (newSpeed: 1 | 2 | 5 | 10) => {
    try {
      if (newSpeed === 1 || newSpeed === 5 || newSpeed === 10) {
        await apiSetSpeed(newSpeed)
      }
    } catch {
      // demo mode
    }
    setSpeed(newSpeed)
    addLogEntry('tick', `Speed changed to ${newSpeed}x`)
  }, [addLogEntry])

  const handleScenarioChange = useCallback(async (newScenario: string) => {
    try {
      await apiSetScenario(newScenario)
    } catch {
      // demo mode
    }
    setScenario(newScenario)
    addLogEntry('tick', `Scenario changed to "${newScenario}"`)
  }, [addLogEntry])

  const handleTriggerAnomaly = useCallback(async () => {
    try {
      await apiTriggerAnomaly('c1')
    } catch {
      // demo mode
    }
    setTickCount((t) => t + 1)
    addLogEntry('trigger', 'Manual anomaly triggered on random campaign')
    toast.warning('Anomaly triggered')
  }, [addLogEntry])

  const handleReset = useCallback(async () => {
    if (!window.confirm('Reset simulation? All current data will be lost.')) return
    try {
      await apiResetSimulation()
    } catch {
      // demo mode
    }
    setSimStatus('stopped')
    setTickCount(0)
    setLogEntries([])
    toast.info('Simulation reset')
  }, [])

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="rounded-lg bg-amber-500/10 p-2">
          <FlaskConical className="h-5 w-5 text-amber-400" />
        </div>
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-100">
            Simulation Controls
          </h1>
          <p className="text-sm text-slate-500">
            Test budget rules with simulated ad spend scenarios
          </p>
        </div>
      </div>

      {/* Status panel */}
      <div className="rounded-xl border border-[#1a1a2e] bg-[#12121a] p-5">
        <div className="mb-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <StatusBadge variant={simStatus} label={simStatus.toUpperCase()} />
            <div className="flex items-center gap-4 text-sm text-slate-400">
              <span className="flex items-center gap-1.5">
                <Clock className="h-3.5 w-3.5" />
                14:23:25
              </span>
              <span className="flex items-center gap-1.5">
                <Hash className="h-3.5 w-3.5" />
                {tickCount} ticks
              </span>
              <span className="flex items-center gap-1.5">
                <Monitor className="h-3.5 w-3.5" />
                5 campaigns
              </span>
            </div>
          </div>
          <SpeedSelector
            currentSpeed={speed}
            onSpeedChange={handleSpeedChange}
            disabled={simStatus === 'stopped'}
          />
        </div>

        {/* Controls */}
        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={handleStartPause}
            disabled={isLoading}
            className={`inline-flex items-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium transition-colors ${
              simStatus === 'running'
                ? 'bg-amber-600 text-white hover:bg-amber-700'
                : 'bg-emerald-600 text-white hover:bg-emerald-700'
            } disabled:opacity-50`}
          >
            {simStatus === 'running' ? (
              <>
                <Pause className="h-4 w-4" />
                Pause
              </>
            ) : (
              <>
                <Play className="h-4 w-4" />
                Start
              </>
            )}
          </button>

          <ScenarioDropdown
            currentScenario={scenario}
            onScenarioChange={handleScenarioChange}
            disabled={simStatus === 'running'}
          />

          <button
            onClick={handleTriggerAnomaly}
            disabled={simStatus !== 'running'}
            className="inline-flex items-center gap-2 rounded-lg border border-amber-500/20 bg-amber-500/10 px-4 py-2.5 text-sm font-medium text-amber-400 transition-colors hover:bg-amber-500/20 disabled:opacity-50"
          >
            <Zap className="h-4 w-4" />
            Trigger Anomaly
          </button>

          <button
            onClick={handleReset}
            className="inline-flex items-center gap-2 rounded-lg border border-red-500/20 bg-red-500/10 px-4 py-2.5 text-sm font-medium text-red-400 transition-colors hover:bg-red-500/20"
          >
            <RotateCcw className="h-4 w-4" />
            Reset
          </button>
        </div>
      </div>

      {/* Event log */}
      <div className="rounded-xl border border-[#1a1a2e] bg-[#12121a] p-5">
        <h3 className="mb-4 text-sm font-semibold text-slate-200">Event Log</h3>
        <SimulationLog entries={logEntries} />
      </div>
    </div>
  )
}
