import { lazy, Suspense } from 'react'
import type { PlotParams } from 'react-plotly.js'

// Lazy-load the heavy Plotly bundle so it never blocks initial render
const Plot = lazy(() =>
  import('react-plotly.js').then((mod: any) => {
    const Component = mod.default?.default || mod.default || mod;
    return { default: Component as React.ComponentType<PlotParams> };
  })
)

export default function Chart(props: PlotParams) {
  return (
    <Suspense fallback={<div className="flex items-center justify-center h-32 text-gray-300 text-sm">Loading chart…</div>}>
      <Plot {...props} />
    </Suspense>
  )
}
