export function stockColor(quantity: number, threshold = 500): string {
  if (quantity === 0) return '#E74C3C'
  if (quantity < 100) return '#E74C3C'
  if (quantity < 300) return '#F39C12'
  if (quantity < threshold) return '#F1C40F'
  return '#27AE60'
}

export function severityLabel(quantity: number): 'Critical' | 'Warning' | 'Caution' | 'Adequate' {
  if (quantity < 100) return 'Critical'
  if (quantity < 300) return 'Warning'
  if (quantity < 500) return 'Caution'
  return 'Adequate'
}

export function severityBadgeClass(label: string): string {
  switch (label) {
    case 'Critical': return 'bg-red-100 text-red-700 border border-red-300'
    case 'Warning': return 'bg-amber-100 text-amber-700 border border-amber-300'
    case 'Caution': return 'bg-yellow-100 text-yellow-700 border border-yellow-300'
    default: return 'bg-green-100 text-green-700 border border-green-300'
  }
}
