import { useMemo, useState } from 'react'
import Chart from '../components/ui/Chart'
import { useStock } from '../hooks/useApiData'
import DataFreshnessBanner from '../components/ui/DataFreshnessBanner'

const COLORS = ['#2563EB', '#DC2626', '#D97706', '#16A34A', '#7C3AED']

export default function Trends() {
  const { data: stock, isLoading } = useStock({ limit: 5000 })
  const [granularity, setGranularity] = useState<'weekly' | 'monthly'>('weekly')

  const { lines, weeklyChange } = useMemo(() => {
    if (!stock) return { lines: [], fertilizers: [], weeklyChange: [] }

    // Group by fertilizer + date, sum quantities
    const byFertDate: Record<string, Record<string, number>> = {}
    for (const r of stock) {
      if (!byFertDate[r.fertilizer_name]) byFertDate[r.fertilizer_name] = {}
      byFertDate[r.fertilizer_name][r.scrape_date] = (byFertDate[r.fertilizer_name][r.scrape_date] ?? 0) + r.quantity
    }

    const fertilizers = Object.keys(byFertDate)
    const allDates = [...new Set(stock.map((r) => r.scrape_date))].sort()

    const lines = fertilizers.map((fert, i) => ({
      type: 'scatter' as const,
      mode: 'lines+markers' as const,
      name: fert,
      x: allDates,
      y: allDates.map((d) => byFertDate[fert][d] ?? null),
      line: { color: COLORS[i % COLORS.length] },
      marker: { size: 8, color: COLORS[i % COLORS.length] },
    }))

    // Week-over-week change
    const weeklyChange = fertilizers.map((fert) => {
      const dates = allDates.slice(-7)
      return {
        fert,
        changes: dates.map((d, idx) => {
          if (idx === 0) return null
          const prev = byFertDate[fert][dates[idx - 1]] ?? 0
          const curr = byFertDate[fert][d] ?? 0
          if (prev === 0) return null
          return (((curr - prev) / prev) * 100).toFixed(1)
        }),
        dates,
      }
    })

    return { lines, fertilizers, weeklyChange }
  }, [stock])

  if (isLoading) return <div className="p-8 text-gray-400">Loading…</div>

  return (
    <div className="space-y-6">
      <DataFreshnessBanner />
      <h1 className="text-2xl font-bold">Weekly Stock Trends</h1>
      <p className="text-sm text-gray-500">Each data point represents one weekly scrape snapshot</p>

      <div className="flex gap-2">
        {(['weekly', 'monthly'] as const).map((g) => (
          <button
            key={g}
            onClick={() => setGranularity(g)}
            className={`px-4 py-1.5 rounded-full text-sm font-medium capitalize ${
              granularity === g ? 'bg-[#1B7A3D] text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {g}
          </button>
        ))}
        <span className="text-xs text-gray-400 self-center ml-2">ⓘ Daily granularity unavailable — data is captured once per week</span>
      </div>

      <div className="bg-white rounded-xl shadow-sm p-4">
        <h2 className="text-sm font-semibold mb-3">State-wide Fertilizer Stock — Weekly Snapshots</h2>
        <Chart
          data={lines}
          layout={{
            height: 380,
            margin: { l: 60, r: 20, t: 10, b: 60 },
            xaxis: { title: { text: 'Scrape Date' }, gridcolor: '#F3F4F6' },
            yaxis: { title: { text: 'Total Stock (kg)' }, gridcolor: '#F3F4F6' },
            legend: { orientation: 'h', y: -0.2 },
            paper_bgcolor: 'transparent',
            plot_bgcolor: '#FAFAFA',
          }}
          config={{ responsive: true, displayModeBar: false }}
          style={{ width: '100%' }}
        />
      </div>

      {/* Week-over-week table */}
      <div className="bg-white rounded-xl shadow-sm p-4">
        <h2 className="text-sm font-semibold mb-1">Week-over-Week Change (%)</h2>
        <p className="text-xs text-gray-400 mb-3">Each column = change from previous scrape run</p>
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-[#1B7A3D] text-white text-xs">
              <th className="p-2 text-left rounded-tl-lg">Fertilizer</th>
              {weeklyChange[0]?.dates.slice(1).map((d) => (
                <th key={d} className="p-2 text-right">{d}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {weeklyChange.map(({ fert, changes }, i) => (
              <tr key={fert} className={i % 2 === 0 ? 'bg-gray-50' : ''}>
                <td className="p-2 text-xs font-medium">{fert}</td>
                {changes.slice(1).map((c, j) => {
                  const val = c ? parseFloat(c) : null
                  return (
                    <td key={j} className={`p-2 text-right text-xs font-medium ${
                      val === null ? 'text-gray-300' :
                      val > 0 ? 'text-green-600' :
                      val < 0 ? 'text-red-600' : 'text-gray-400'
                    } ${val && Math.abs(val) >= 10 ? 'font-bold' : ''}`}>
                      {val !== null ? `${val > 0 ? '+' : ''}${c}%` : '—'}
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
