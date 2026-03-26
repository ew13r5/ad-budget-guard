import {
  ResponsiveContainer,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  Area,
  ComposedChart,
} from 'recharts'

interface DataPoint {
  time: string
  actual: number
  forecast?: number
}

interface ForecastChartProps {
  data: DataPoint[]
  budget: number
}

export function ForecastChart({ data, budget }: ForecastChartProps) {
  const threshold80 = budget * 0.8
  const threshold95 = budget * 0.95

  return (
    <div className="rounded-xl border border-[#1a1a2e] bg-[#12121a] p-5">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-200">Spend Forecast</h3>
        <div className="flex items-center gap-4 text-xs text-slate-500">
          <div className="flex items-center gap-1.5">
            <div className="h-2 w-4 rounded-full bg-blue-500" />
            Actual
          </div>
          <div className="flex items-center gap-1.5">
            <div className="h-0.5 w-4 border-t-2 border-dashed border-blue-500/50" />
            Forecast
          </div>
          <div className="flex items-center gap-1.5">
            <div className="h-2 w-4 rounded-full bg-red-500/30" />
            Budget
          </div>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={280}>
        <ComposedChart data={data} margin={{ top: 10, right: 10, bottom: 0, left: 10 }}>
          <defs>
            <linearGradient id="actualGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.3} />
              <stop offset="100%" stopColor="#3b82f6" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#1a1a2e" vertical={false} />
          <XAxis
            dataKey="time"
            tick={{ fontSize: 11, fill: '#64748b' }}
            axisLine={{ stroke: '#1a1a2e' }}
            tickLine={false}
          />
          <YAxis
            tick={{ fontSize: 11, fill: '#64748b' }}
            axisLine={false}
            tickLine={false}
            domain={[0, budget * 1.2]}
            tickFormatter={(v: number) => `$${v}`}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1a1a2e',
              border: '1px solid #2a2a3e',
              borderRadius: '8px',
              color: '#e2e8f0',
              fontSize: '12px',
            }}
            formatter={(value) => [`$${Number(value).toFixed(2)}`, '']}
          />
          <ReferenceLine
            y={threshold80}
            stroke="#f59e0b"
            strokeDasharray="4 4"
            strokeOpacity={0.5}
            label={{ value: '80%', position: 'right', fill: '#f59e0b', fontSize: 10 }}
          />
          <ReferenceLine
            y={threshold95}
            stroke="#ef4444"
            strokeDasharray="4 4"
            strokeOpacity={0.5}
            label={{ value: '95%', position: 'right', fill: '#ef4444', fontSize: 10 }}
          />
          <ReferenceLine
            y={budget}
            stroke="#ef4444"
            strokeWidth={2}
            strokeOpacity={0.7}
            label={{ value: 'Budget', position: 'right', fill: '#ef4444', fontSize: 10 }}
          />
          <Area
            type="monotone"
            dataKey="actual"
            fill="url(#actualGradient)"
            stroke="none"
            isAnimationActive={false}
          />
          <Line
            type="monotone"
            dataKey="actual"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={false}
            isAnimationActive={false}
          />
          <Line
            type="monotone"
            dataKey="forecast"
            stroke="#3b82f6"
            strokeWidth={2}
            strokeDasharray="6 4"
            strokeOpacity={0.5}
            dot={false}
            isAnimationActive={false}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}
