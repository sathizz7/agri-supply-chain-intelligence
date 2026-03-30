import { useMemo } from 'react'
import Chart from '../components/ui/Chart'
import { Link } from 'react-router-dom'
import { useStock } from '../hooks/useApiData'
import DataFreshnessBanner from '../components/ui/DataFreshnessBanner'

const COLORS = ['#1B7A3D','#2563EB','#DC2626','#D97706','#7C3AED','#0891B2','#BE185D','#65A30D']

export default function DeepDive() {
  const { data: stock, isLoading } = useStock({ limit: 5000 })

  const { byFertilizer, topDealers } = useMemo(() => {
    if (!stock) return { byFertilizer: {} as Record<string, number>, topDealers: [] }

    const byFertilizer: Record<string, number> = {}
    const byDealer: Record<string, { name: string; district: string; block: string; total: number }> = {}

    for (const r of stock) {
      byFertilizer[r.fertilizer_name] = (byFertilizer[r.fertilizer_name] ?? 0) + r.quantity
      if (!byDealer[r.dealer_code]) byDealer[r.dealer_code] = { name: r.dealer_name, district: r.district_name, block: r.block_name, total: 0 }
      byDealer[r.dealer_code].total += r.quantity
    }

    const topDealers = Object.entries(byDealer)
      .map(([code, d]) => ({ code, ...d }))
      .sort((a, b) => b.total - a.total)
      .slice(0, 20)

    return { byFertilizer, topDealers }
  }, [stock])

  const fertilizers = Object.keys(byFertilizer)
  const values = fertilizers.map((f) => byFertilizer[f])

  if (isLoading) return <div className="p-8 text-gray-400">Loading…</div>

  return (
    <div className="space-y-6">
      <DataFreshnessBanner />
      <h1 className="text-2xl font-bold">Fertilizer-wise Availability</h1>

      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-2 bg-white rounded-xl shadow-sm p-4">
          <h2 className="text-sm font-semibold mb-3">Stock by Fertilizer Type</h2>
          <Chart
            data={[{ type: 'bar', x: fertilizers, y: values, marker: { color: COLORS } }]}
            layout={{ height: 300, margin: { l: 60, r: 20, t: 10, b: 80 }, xaxis: { tickangle: -45 }, paper_bgcolor: 'transparent', plot_bgcolor: '#FAFAFA' }}
            config={{ responsive: true, displayModeBar: false }}
            style={{ width: '100%' }}
          />
        </div>
        <div className="bg-white rounded-xl shadow-sm p-4">
          <h2 className="text-sm font-semibold mb-3">Stock Share by Fertilizer</h2>
          <Chart
            data={[{ type: 'pie', labels: fertilizers, values, hole: 0.5, marker: { colors: COLORS } }]}
            layout={{ height: 280, margin: { l: 0, r: 0, t: 0, b: 0 }, showlegend: false, paper_bgcolor: 'transparent' }}
            config={{ responsive: true, displayModeBar: false }}
            style={{ width: '100%' }}
          />
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm p-4">
        <h2 className="text-sm font-semibold mb-3">Top 20 Dealers by Total Stock</h2>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-gray-500 uppercase border-b">
              <th className="pb-2">#</th>
              <th className="pb-2">Dealer</th>
              <th className="pb-2">Block</th>
              <th className="pb-2">District</th>
              <th className="pb-2 text-right">Total Stock (kg)</th>
            </tr>
          </thead>
          <tbody>
            {topDealers.map((d, i) => (
              <tr key={d.code} className={`border-b last:border-0 ${i % 2 === 0 ? 'bg-gray-50' : ''}`}>
                <td className="py-2 text-gray-400 text-xs">{i + 1}</td>
                <td className="py-2">
                  <Link to={`/dealers/${d.code}`} className="text-[#1B7A3D] hover:underline text-xs">{d.name}</Link>
                </td>
                <td className="py-2 text-xs text-gray-500">{d.block}</td>
                <td className="py-2 text-xs text-gray-500">{d.district}</td>
                <td className="py-2 text-right font-semibold">{d.total.toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
