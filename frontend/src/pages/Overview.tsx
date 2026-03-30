import { useMemo } from 'react'
import Chart from '../components/ui/Chart'
import { Link } from 'react-router-dom'
import { useSummary } from '../hooks/useApiData'
import { useFilterStore } from '../store/filterStore'
import KPICard from '../components/ui/KPICard'
import DataFreshnessBanner from '../components/ui/DataFreshnessBanner'
import { stockColor } from '../utils/stockColor'

export default function Overview() {
  const { data: summary, isLoading } = useSummary()
  const threshold = useFilterStore((s) => s.lowStockThreshold)

  const kpis = useMemo(() => {
    if (!summary) return null
    const totalStock = summary.reduce((a, d) => a + d.total_stock_kg, 0)
    const totalDealers = summary.reduce((a, d) => a + d.total_dealers, 0)
    const alerts = summary.filter((d) => d.total_stock_kg < threshold * d.total_dealers).length
    return { districts: summary.length, dealers: totalDealers, stockMT: (totalStock / 1000).toFixed(1), alerts }
  }, [summary, threshold])

  const topDistricts = useMemo(() => {
    if (!summary) return []
    return [...summary].sort((a, b) => b.total_stock_kg - a.total_stock_kg).slice(0, 10)
  }, [summary])

  if (isLoading) return <div className="p-8 text-gray-400">Loading…</div>

  return (
    <div className="space-y-6">
      <DataFreshnessBanner />

      <h1 className="text-2xl font-bold text-gray-900">District-wise Fertilizer Availability</h1>

      {kpis && (
        <div className="grid grid-cols-4 gap-4">
          <KPICard label="Total Districts" value={kpis.districts} />
          <KPICard label="Active Dealers" value={kpis.dealers.toLocaleString()} />
          <KPICard label="Total Stock" value={`${kpis.stockMT} T`} />
          <KPICard label="Low-Stock Districts" value={kpis.alerts} accent="border-red-500" deltaType="up-bad" />
        </div>
      )}

      <div className="grid grid-cols-3 gap-6">
        {/* Bar Chart */}
        <div className="col-span-2 bg-white rounded-xl shadow-sm p-4">
          <h2 className="text-sm font-semibold text-gray-700 mb-3">Top 10 Districts by Stock</h2>
          {topDistricts.length > 0 && (
            <Chart
              data={[{
                type: 'bar',
                orientation: 'h',
                y: topDistricts.map((d) => d.district_name),
                x: topDistricts.map((d) => d.total_stock_kg),
                marker: { color: topDistricts.map((d) => stockColor(d.total_stock_kg / Math.max(d.total_dealers, 1))) },
              }]}
              layout={{ height: 300, margin: { l: 140, r: 20, t: 10, b: 40 }, xaxis: { title: { text: 'Total Stock (kg)' } }, yaxis: { automargin: true }, paper_bgcolor: 'transparent', plot_bgcolor: 'transparent' }}
              config={{ responsive: true, displayModeBar: false }}
              style={{ width: '100%' }}
            />
          )}
        </div>

        {/* Summary stats */}
        <div className="bg-white rounded-xl shadow-sm p-4">
          <h2 className="text-sm font-semibold text-gray-700 mb-3">Quick Stats</h2>
          <div className="space-y-2">
            {summary?.slice(0, 8).map((d) => (
              <div key={d.district_code} className="flex items-center justify-between text-sm">
                <Link to={`/map?district=${d.district_code}`} className="text-[#1B7A3D] hover:underline truncate max-w-[140px]">
                  {d.district_name}
                </Link>
                <span className="text-gray-600 text-xs">{d.total_dealers} dealers</span>
              </div>
            ))}
          </div>
          <Link to="/map" className="mt-4 block text-xs text-[#1B7A3D] hover:underline">Explore Full Map →</Link>
        </div>
      </div>

      {/* Summary table */}
      <div className="bg-white rounded-xl shadow-sm p-4">
        <h2 className="text-sm font-semibold text-gray-700 mb-3">Week-over-Week Summary</h2>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-gray-500 uppercase border-b">
              <th className="pb-2">District</th>
              <th className="pb-2 text-right">Dealers</th>
              <th className="pb-2 text-right">Total Stock (kg)</th>
              <th className="pb-2">Last Scraped</th>
            </tr>
          </thead>
          <tbody>
            {summary?.map((d, i) => (
              <tr key={d.district_code} className={`border-b last:border-0 ${i % 2 === 0 ? 'bg-gray-50' : ''}`}>
                <td className="py-2">
                  <Link to={`/dealers?district=${d.district_code}`} className="text-[#1B7A3D] hover:underline">
                    {d.district_name}
                  </Link>
                </td>
                <td className="py-2 text-right text-gray-600">{d.total_dealers}</td>
                <td className="py-2 text-right font-medium">{d.total_stock_kg.toLocaleString()}</td>
                <td className="py-2 text-gray-400 text-xs">{d.last_scraped ?? '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
