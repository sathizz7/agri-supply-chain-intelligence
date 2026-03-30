import { useMemo } from 'react'
import Chart from '../components/ui/Chart'
import { useStock } from '../hooks/useApiData'
import DataFreshnessBanner from '../components/ui/DataFreshnessBanner'

export default function SupplyMatrix() {
  const { data: stock, isLoading } = useStock({ limit: 5000 })

  const { districts, fertilizers, matrix, zeros } = useMemo(() => {
    if (!stock) return { districts: [], fertilizers: [], matrix: [], zeros: [] }

    const pivot: Record<string, Record<string, number>> = {}
    for (const r of stock) {
      if (!pivot[r.district_name]) pivot[r.district_name] = {}
      pivot[r.district_name][r.fertilizer_name] = (pivot[r.district_name][r.fertilizer_name] ?? 0) + r.quantity
    }

    const districts = Object.keys(pivot)
    const fertilizers = [...new Set(stock.map((r) => r.fertilizer_name))]
    const matrix = districts.map((d) => fertilizers.map((f) => pivot[d][f] ?? 0))

    const zeros: Array<{ district: string; fertilizer: string }> = []
    for (const d of districts) {
      for (const f of fertilizers) {
        if (!pivot[d]?.[f]) zeros.push({ district: d, fertilizer: f })
      }
    }

    return { districts, fertilizers, matrix, zeros }
  }, [stock])

  if (isLoading) return <div className="p-8 text-gray-400">Loading…</div>

  return (
    <div className="space-y-6">
      <DataFreshnessBanner />
      <h1 className="text-2xl font-bold">Supply Matrix: District × Fertilizer</h1>

      {zeros.length > 0 && (
        <div className="bg-amber-50 border border-amber-300 rounded-lg px-4 py-3 text-sm text-amber-800">
          ⚠️ <strong>{zeros.length}</strong> district-fertilizer combinations have ZERO stock.
        </div>
      )}

      <div className="bg-white rounded-xl shadow-sm p-4">
        <Chart
          data={[{
            type: 'heatmap',
            z: matrix,
            x: fertilizers,
            y: districts,
            colorscale: 'RdYlGn',
            hoverongaps: false,
          }]}
          layout={{
            height: Math.max(400, districts.length * 22),
            margin: { l: 160, r: 60, t: 30, b: 100 },
            xaxis: { tickangle: -45 },
            yaxis: { automargin: true },
            paper_bgcolor: 'transparent',
          }}
          config={{ responsive: true, displayModeBar: false }}
          style={{ width: '100%' }}
        />
      </div>

      {zeros.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm p-4">
          <h2 className="text-sm font-semibold mb-3">Zero-Stock Combinations ({zeros.length})</h2>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-gray-500 uppercase border-b">
                <th className="pb-2">District</th>
                <th className="pb-2">Fertilizer</th>
              </tr>
            </thead>
            <tbody>
              {zeros.slice(0, 50).map((z, i) => (
                <tr key={i} className={`border-b last:border-0 ${i % 2 === 0 ? 'bg-gray-50' : ''}`}>
                  <td className="py-1.5 text-xs">{z.district}</td>
                  <td className="py-1.5 text-xs">{z.fertilizer}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
