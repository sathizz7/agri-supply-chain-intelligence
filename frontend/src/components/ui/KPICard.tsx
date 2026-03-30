interface Props {
  label: string
  value: string | number
  delta?: string
  deltaType?: 'up-good' | 'up-bad' | 'neutral'
  accent?: string
}

export default function KPICard({ label, value, delta, deltaType = 'neutral', accent }: Props) {
  const deltaColor =
    deltaType === 'up-good' ? 'text-green-600 bg-green-50' :
    deltaType === 'up-bad' ? 'text-red-600 bg-red-50' :
    'text-gray-500 bg-gray-50'

  return (
    <div className={`bg-white rounded-xl shadow-sm border-l-4 p-4 ${accent ?? 'border-[#1B7A3D]'}`}>
      <p className="text-xs text-gray-500 font-medium uppercase tracking-wide">{label}</p>
      <p className="text-3xl font-bold text-gray-900 mt-1">{value}</p>
      {delta && (
        <span className={`text-xs font-medium px-1.5 py-0.5 rounded mt-1 inline-block ${deltaColor}`}>
          {delta}
        </span>
      )}
    </div>
  )
}
