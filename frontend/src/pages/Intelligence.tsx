import { useMemo, useState } from 'react'
import Chart from '../components/ui/Chart'
import { useStock } from '../hooks/useApiData'
import DataFreshnessBanner from '../components/ui/DataFreshnessBanner'

const tabs = ['Stock Concentration', 'Coverage Gaps', 'Stock Volatility']

export default function Intelligence() {
  const [tab, setTab] = useState(0)
  const { data: stock, isLoading } = useStock({ limit: 5000 })

  const concentration = useMemo(() => {
    if (!stock) return []
    const byDistFert: Record<string, Record<string, Record<string, number>>> = {}
    for (const r of stock) {
      if (!byDistFert[r.district_name]) byDistFert[r.district_name] = {}
      if (!byDistFert[r.district_name][r.fertilizer_name]) byDistFert[r.district_name][r.fertilizer_name] = {}
      byDistFert[r.district_name][r.fertilizer_name][r.dealer_code] =
        (byDistFert[r.district_name][r.fertilizer_name][r.dealer_code] ?? 0) + r.quantity
    }
    return Object.entries(byDistFert).map(([district, ferts]) => {
      const ureaData = ferts['யூரியா'] ?? ferts[Object.keys(ferts)[0]] ?? {}
      const total = Object.values(ureaData).reduce((a, b) => a + b, 0)
      const top5 = Object.values(ureaData).sort((a, b) => b - a).slice(0, 5).reduce((a, b) => a + b, 0)
      const pct = total > 0 ? Math.round((top5 / total) * 100) : 0
      return { district, pct, dealers: Object.entries(ureaData).sort(([, a], [, b]) => b - a).slice(0, 5) }
    }).sort((a, b) => b.pct - a.pct)
  }, [stock])

  if (isLoading) return <div className="p-8 text-gray-400">Loading…</div>

  return (
    <div className="space-y-6">
      <DataFreshnessBanner />
      <h1 className="text-2xl font-bold">Supply Intelligence</h1>
      <p className="text-sm text-gray-500">Data-driven insights for supply chain decision-making</p>

      <div className="flex gap-1 bg-gray-100 p-1 rounded-lg w-fit">
        {tabs.map((t, i) => (
          <button
            key={t}
            onClick={() => setTab(i)}
            disabled={i === 2}
            className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${
              tab === i ? 'bg-[#1B7A3D] text-white' :
              i === 2 ? 'text-gray-300 cursor-not-allowed' :
              'text-gray-600 hover:bg-white'
            }`}
          >
            {t}{i === 2 ? ' 🔒' : ''}
          </button>
        ))}
      </div>

      {tab === 0 && (
        <div className="space-y-4">
          <p className="text-sm text-gray-600">Shows what % of a fertilizer's stock is held by top-5 dealers (monopoly risk)</p>
          {concentration.map(({ district, pct, dealers }) => (
            <div key={district} className="bg-white rounded-xl shadow-sm border border-gray-100">
              <div className="flex items-center gap-3 p-4">
                <span className="text-lg">{pct > 80 ? '🔴' : pct > 60 ? '🟡' : '🟢'}</span>
                <span className="font-medium text-sm">{district}</span>
                <span className="text-xs text-gray-500 ml-auto">Top 5 hold <strong>{pct}%</strong></span>
              </div>
              {pct > 80 && dealers.length > 0 && (
                <div className="px-4 pb-4 border-t border-gray-50">
                  <Chart
                    data={[{ type: 'pie', labels: dealers.map(([code]) => code), values: dealers.map(([, v]) => v), hole: 0.4 }]}
                    layout={{ height: 200, margin: { l: 0, r: 0, t: 10, b: 0 }, showlegend: true, paper_bgcolor: 'transparent' }}
                    config={{ responsive: true, displayModeBar: false }}
                    style={{ width: '100%' }}
                  />
                  <p className="text-xs text-red-600 mt-2">High concentration risk: {pct}% held by top 5 dealers</p>
                </div>
              )}
            </div>
          ))}
          {concentration.filter((c) => c.pct > 80).length > 0 && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-sm text-green-800">
              {concentration.filter((c) => c.pct > 80).length} of {concentration.length} districts have high concentration risk (&gt;80%).
              Consider diversifying dealer allocation.
            </div>
          )}
        </div>
      )}

      {tab === 1 && (
        <div className="space-y-4">
          <p className="text-sm text-gray-600">Districts and blocks with zero stock for any fertilizer type</p>
          <div className="bg-white rounded-xl shadow-sm p-4 text-sm text-gray-500">
            Switch to Supply Matrix page for detailed zero-stock heatmap →
          </div>
        </div>
      )}

      {tab === 2 && (
        <div className="flex items-center justify-center py-16">
          <div className="text-center max-w-md">
            <div className="text-5xl mb-4">📊</div>
            <h2 className="text-xl font-bold text-gray-800">Stock Volatility Analysis</h2>
            <p className="text-gray-500 text-sm mt-2">Requires 8 or more weekly scrape runs to compute meaningful volatility scores</p>
            <div className="mt-6">
              <p className="text-xs text-gray-400 mb-2">Data collection progress</p>
              <div className="w-full bg-gray-100 rounded-full h-2">
                <div className="bg-[#1B7A3D] h-2 rounded-full" style={{ width: '37%' }} />
              </div>
              <p className="text-xs text-gray-400 mt-1">3 of 8 required scrape runs completed</p>
            </div>
            <ul className="text-xs text-gray-400 mt-4 text-left list-disc list-inside space-y-1">
              <li>Coefficient of variation (σ/μ) per dealer per fertilizer</li>
              <li>Dealers with erratic supply patterns flagged</li>
              <li>District-level supply reliability scores</li>
            </ul>
            <p className="text-xs text-gray-300 mt-4">Available from Run #9 onwards</p>
          </div>
        </div>
      )}
    </div>
  )
}
