import { severityBadgeClass, severityLabel } from '../../utils/stockColor'

interface Props { quantity: number }

export default function SeverityBadge({ quantity }: Props) {
  const label = severityLabel(quantity)
  return (
    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${severityBadgeClass(label)}`}>
      {label}
    </span>
  )
}
