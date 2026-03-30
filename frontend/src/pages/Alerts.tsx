import { useMemo } from 'react'
import { Link } from 'react-router-dom'
import { useStock } from '../hooks/useApiData'
import { useFilterStore } from '../store/filterStore'
import SeverityBadge from '../components/ui/SeverityBadge'
import DataFreshnessBanner from '../components/ui/DataFreshnessBanner'

export default function Alerts() {
  const { data: stock, isLoading } = useStock({ limit: 5000 })
  const threshold = useFilterStore((s) => s.lowStockThreshold)

  const alerts = useMemo(() => {
    if (!stock) return []
    return stock.filter((r) => r.quantity < threshold && r.quantity >= 0)
      .sort((a, b) => a.quantity - b.quantity)
  }, [stock, threshold])

  const critical = alerts.filter((r) => r.quantity < 100)
  const warning = alerts.filter((r) => r.quantity >= 100 && r.quantity < 300)
  const caution = alerts.filter((r) => r.quantity >= 300)

  if (isLoading) return <div className="p-8 text-gray-400">Loading…</div>

  return (
    <div className="space-y-6">
      <DataFreshnessBanner />

      <div className="bg-amber-50 border-l-4 border-amber-400 rounded-lg px-4 py-3">
        <p className="text-amber-800 font-medium">⚠️ Alerts are from the latest scrape run only.</p>
        <p className="text-amber-700 text-sm mt-0.5">Contact dealers to confirm current availability before acting on this data.</p>
      </div>

      <h1 className="text-2xl font-bold">Low-Stock Alerts</h1>
      <p className="text-sm text-gray-500">Showing dealers below {threshold} kg threshold</p>

      <div className="grid grid-cols-3 gap-4">
        {[
          { label: 'Critical (<100 kg)', count: critical.length, color: 'border-red-500 bg-red-50', text: 'text-red-700' },
          { label: 'Warning (<300 kg)', count: warning.length, color: 'border-amber-500 bg-amber-50', text: 'text-amber-700' },
          { label: `Caution (<${threshold} kg)`, count: caution.length, color: 'border-yellow-500 bg-yellow-50', text: 'text-yellow-700' },
        ].map((s) => (
          <div key={s.label} className={`rounded-xl border-l-4 p-5 ${s.color}`}>
            <p className={`text-xs font-medium uppercase tracking-wide ${s.text}`}>{s.label}</p>
            <p className={`text-4xl font-bold mt-1 ${s.text}`}>{s.count}</p>
          </div>
        ))}
      </div>

      <div className="bg-white rounded-xl shadow-sm p-4">
        <h2 className="text-sm font-semibold mb-3">Alert Details</h2>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-gray-500 uppercase border-b">
              <th className="pb-2">Severity</th>
              <th className="pb-2">District</th>
              <th className="pb-2">Block</th>
              <th className="pb-2">Dealer</th>
              <th className="pb-2">Fertilizer</th>
              <th className="pb-2 text-right">Stock (kg)</th>
            </tr>
          </thead>
          <tbody>
            {alerts.slice(0, 100).map((r, i) => (
              <tr key={i} className={`border-b last:border-0 ${i % 2 === 0 ? 'bg-gray-50' : ''}`}>
                <td className="py-2"><SeverityBadge quantity={r.quantity} /></td>
                <td className="py-2 text-xs">{r.district_name}</td>
                <td className="py-2 text-xs">{r.block_name}</td>
                <td className="py-2">
                  <Link to={`/dealers/${r.dealer_code}`} className="text-[#1B7A3D] hover:underline text-xs">
                    {r.dealer_name}
                  </Link>
                </td>
                <td className="py-2 text-xs">{r.fertilizer_name}</td>
                <td className="py-2 text-right font-bold text-red-600">{r.quantity}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
