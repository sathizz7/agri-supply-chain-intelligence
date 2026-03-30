import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useStock } from '../hooks/useApiData'
import SeverityBadge from '../components/ui/SeverityBadge'

export default function Dealers() {
  const { data: stock, isLoading } = useStock({ limit: 5000 })
  const [search, setSearch] = useState('')

  const dealers = stock
    ? [...new Map(stock.map((r) => [r.dealer_code, r])).values()]
        .filter((d) => !search || d.dealer_code.includes(search) || d.dealer_name.includes(search))
    : []

  const minStock = (code: string) => {
    const records = stock?.filter((r) => r.dealer_code === code) ?? []
    return records.length ? Math.min(...records.map((r) => r.quantity)) : 0
  }

  if (isLoading) return <div className="p-8 text-gray-400">Loading…</div>

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Dealer Directory</h1>

      <div className="flex gap-3">
        <input
          type="text"
          placeholder="Search by dealer code or name…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="flex-1 border border-gray-200 rounded-lg px-4 py-2 text-sm"
        />
      </div>

      <div className="bg-white rounded-xl shadow-sm p-4">
        <p className="text-xs text-gray-400 mb-3">{dealers.length} dealers</p>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-gray-500 uppercase border-b">
              <th className="pb-2">Code</th>
              <th className="pb-2">Dealer Name</th>
              <th className="pb-2">Block</th>
              <th className="pb-2">District</th>
              <th className="pb-2">Status</th>
            </tr>
          </thead>
          <tbody>
            {dealers.slice(0, 100).map((d, i) => (
              <tr key={d.dealer_code} className={`border-b last:border-0 ${i % 2 === 0 ? 'bg-gray-50' : ''}`}>
                <td className="py-2">
                  <Link to={`/dealers/${d.dealer_code}`} className="text-[#1B7A3D] hover:underline font-mono text-xs">
                    {d.dealer_code || '—'}
                  </Link>
                </td>
                <td className="py-2 text-xs">{d.dealer_name}</td>
                <td className="py-2 text-xs text-gray-500">{d.block_name}</td>
                <td className="py-2 text-xs text-gray-500">{d.district_name}</td>
                <td className="py-2"><SeverityBadge quantity={minStock(d.dealer_code)} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
