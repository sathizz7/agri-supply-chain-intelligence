import { useSummary } from '../../hooks/useApiData'

export default function DataFreshnessBanner() {
  const { data } = useSummary()
  const lastScraped = data?.[0]?.last_scraped

  return (
    <div className="flex items-center gap-3 bg-amber-50 border border-amber-200 rounded-lg px-4 py-2.5 mb-4 text-sm">
      <span>📅</span>
      <span className="text-amber-800">
        <span className="font-medium">Showing weekly snapshot data.</span>{' '}
        {lastScraped
          ? <>Last scraped: <strong>{lastScraped}</strong>. Stock conditions may have changed since this snapshot.</>
          : 'Load a district or run the scraper to see data.'}
      </span>
    </div>
  )
}
