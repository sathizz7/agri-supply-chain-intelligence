import { useDistricts, useHealth } from '../../hooks/useApiData'
import { useFilterStore } from '../../store/filterStore'

export default function TopBar() {
  const { data: districts } = useDistricts()
  const { data: health } = useHealth()
  const { selectedDate, selectedDistrictCode, lowStockThreshold, setDate, setDistrict, setThreshold } = useFilterStore()

  return (
    <header className="h-14 bg-white border-b border-gray-200 flex items-center gap-4 px-6 shrink-0">
      <div className="flex items-center gap-2 text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-3 py-1.5">
        <span>📅</span>
        <span className="font-medium">Weekly snapshot data</span>
      </div>

      <div className="flex items-center gap-2 ml-auto">
        <label className="text-xs text-gray-500">Date</label>
        <input
          type="date"
          value={selectedDate ?? ''}
          onChange={(e) => setDate(e.target.value || null)}
          className="text-xs border border-gray-200 rounded px-2 py-1"
        />

        <label className="text-xs text-gray-500">District</label>
        <select
          value={selectedDistrictCode ?? ''}
          onChange={(e) => setDistrict(e.target.value || null)}
          className="text-xs border border-gray-200 rounded px-2 py-1 max-w-[150px]"
        >
          <option value="">All Districts</option>
          {districts?.map((d) => (
            <option key={d.code} value={d.code}>{d.name_ta}</option>
          ))}
        </select>

        <label className="text-xs text-gray-500">Threshold</label>
        <input
          type="number"
          value={lowStockThreshold}
          onChange={(e) => setThreshold(Number(e.target.value))}
          className="text-xs border border-gray-200 rounded px-2 py-1 w-20"
        />

        <div className={`w-2.5 h-2.5 rounded-full ${health?.status === 'ok' ? 'bg-green-500' : 'bg-red-500'}`} title={health?.status} />
      </div>
    </header>
  )
}
