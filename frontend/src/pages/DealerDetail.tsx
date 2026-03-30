import { useMemo } from 'react'
import { useParams, Link } from 'react-router-dom'
import Chart from '../components/ui/Chart'
import { useDealerDetails } from '../hooks/useApiData'
import SeverityBadge from '../components/ui/SeverityBadge'
import DataFreshnessBanner from '../components/ui/DataFreshnessBanner'

const COLORS = ['#2563EB', '#DC2626', '#D97706', '#16A34A']

export default function DealerDetail() {
  const { dealerCode } = useParams<{ dealerCode: string }>()
  const { data: dealer, isLoading } = useDealerDetails(dealerCode ?? '')

  const { fertilizers, chartData, latestStock } = useMemo(() => {
    if (!dealer) return { fertilizers: [], chartData: [], latestStock: {} as Record<string, number> }
    const fertilizers = [...new Set(dealer.stock_history.map((s) => s.fertilizer_name))]
    const dates = [...new Set(dealer.stock_history.map((s) => s.scrape_date))].sort()

    const chartData = fertilizers.map((fert, i) => {
      const byDate: Record<string, number> = {}
      dealer.stock_history.filter((s) => s.fertilizer_name === fert).forEach((s) => { byDate[s.scrape_date] = s.quantity })
      return {
        type: 'bar' as const,
        name: fert,
        x: dates,
        y: dates.map((d) => byDate[d] ?? 0),
        marker: { color: COLORS[i % COLORS.length] },
      }
    })

    const latestStock: Record<string, number> = {}
    for (const fert of fertilizers) {
      const records = dealer.stock_history.filter((s) => s.fertilizer_name === fert).sort((a, b) => b.scrape_date.localeCompare(a.scrape_date))
      if (records[0]) latestStock[fert] = records[0].quantity
    }

    return { fertilizers, chartData, latestStock }
  }, [dealer])

  if (isLoading) return <div className="p-8 text-gray-400">Loading…</div>
  if (!dealer) return <div className="p-8 text-red-500">Dealer not found</div>

  return (
    <div className="space-y-6">
      <DataFreshnessBanner />
      <div className="text-xs text-gray-400">
        <Link to="/dealers" className="hover:text-[#1B7A3D]">Dealers</Link> / {dealer.dealer_code}
      </div>

      <div className="bg-white rounded-xl shadow-sm p-6">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold">{dealer.name_ta}</h1>
              <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded font-mono">#{dealer.dealer_code}</span>
            </div>
            <div className="flex gap-6 mt-3 text-sm text-gray-600">
              <span>📍 {dealer.block_name}</span>
              <span>🗺 {dealer.district_name}</span>
              {dealer.contact && <a href={`tel:${dealer.contact}`} className="text-[#1B7A3D] hover:underline">📞 {dealer.contact}</a>}
            </div>
            {dealer.address && <p className="text-xs text-gray-400 mt-1">{dealer.address}</p>}
          </div>
          <div className="flex gap-2">
            <button className="text-xs border border-[#1B7A3D] text-[#1B7A3D] px-3 py-1.5 rounded-lg hover:bg-green-50">View on Map</button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-4">
        {fertilizers.map((fert) => {
          const qty = latestStock[fert] ?? 0
          return (
            <div key={fert} className="bg-white rounded-xl shadow-sm p-4">
              <p className="text-xs text-gray-500 font-medium uppercase">{fert}</p>
              <p className={`text-2xl font-bold mt-1 ${qty < 100 ? 'text-red-600' : qty < 300 ? 'text-amber-600' : 'text-green-700'}`}>
                {qty.toLocaleString()} kg
              </p>
              <SeverityBadge quantity={qty} />
            </div>
          )
        })}
      </div>

      <div className="bg-white rounded-xl shadow-sm p-4">
        <h2 className="text-sm font-semibold mb-1">Weekly Stock History — Last 8 Scrape Runs</h2>
        <p className="text-xs text-gray-400 mb-3">Each group = one scrape run (weekly snapshot)</p>
        <Chart
          data={[
            ...chartData,
            { type: 'scatter', mode: 'lines', name: '⚠ Critical threshold', x: chartData[0]?.x ?? [], y: (chartData[0]?.x ?? []).map(() => 100), line: { color: '#E74C3C', dash: 'dash', width: 1 }, showlegend: true },
          ]}
          layout={{
            barmode: 'group',
            height: 360,
            margin: { l: 60, r: 20, t: 10, b: 80 },
            xaxis: { title: { text: 'Scrape Date' } },
            yaxis: { title: { text: 'Quantity (kg)' } },
            legend: { orientation: 'h', y: -0.25 },
            paper_bgcolor: 'transparent',
            plot_bgcolor: '#FAFAFA',
          }}
          config={{ responsive: true, displayModeBar: false }}
          style={{ width: '100%' }}
        />
      </div>

      <div className="bg-white rounded-xl shadow-sm p-4">
        <h2 className="text-sm font-semibold mb-3">Stock Records by Scrape Run</h2>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-gray-500 uppercase border-b">
              <th className="pb-2">Date</th>
              <th className="pb-2">Fertilizer</th>
              <th className="pb-2 text-right">Qty (kg)</th>
              <th className="pb-2">Status</th>
            </tr>
          </thead>
          <tbody>
            {dealer.stock_history.map((s, i) => (
              <tr key={i} className={`border-b last:border-0 ${i % 2 === 0 ? 'bg-gray-50' : ''}`}>
                <td className="py-1.5 text-xs text-gray-500">{s.scrape_date}</td>
                <td className="py-1.5 text-xs">{s.fertilizer_name}</td>
                <td className="py-1.5 text-right font-medium">{s.quantity}</td>
                <td className="py-1.5"><SeverityBadge quantity={s.quantity} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
