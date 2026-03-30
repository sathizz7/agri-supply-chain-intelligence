import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Map from 'ol/Map'
import View from 'ol/View'
import TileLayer from 'ol/layer/Tile'
import VectorLayer from 'ol/layer/Vector'
import VectorSource from 'ol/source/Vector'
import OSM from 'ol/source/OSM'
import GeoJSON from 'ol/format/GeoJSON'
import { Style, Fill, Stroke, Text } from 'ol/style'
import { fromLonLat } from 'ol/proj'
import { extend, createEmpty } from 'ol/extent'
import type { FeatureLike } from 'ol/Feature'
import 'ol/ol.css'

import { useSummary } from '../hooks/useApiData'
import { useFilterStore } from '../store/filterStore'
import { stockColor } from '../utils/stockColor'
import type { DistrictSummary } from '../types/api'

interface PanelData {
  name_ta: string
  name_en: string
  scraper_code: string
  summary: DistrictSummary | null
}

export default function MapExplorer() {
  const mapRef = useRef<HTMLDivElement>(null)
  const olMap = useRef<Map | null>(null)
  const vectorLayer = useRef<VectorLayer | null>(null)

  const [panel, setPanel] = useState<PanelData | null>(null)
  const [hoveredCode, setHoveredCode] = useState<string | null>(null)

  const { data: summary } = useSummary()
  const { setDistrict } = useFilterStore()
  const navigate = useNavigate()

  const summaryMapRef = useRef<Record<string, DistrictSummary>>({})
  if (summary) {
    summaryMapRef.current = {}
    summary.forEach((s) => { summaryMapRef.current[s.district_code] = s })
  }

  function makeStyle(feature: FeatureLike, isHovered: boolean): Style {
    const code: string = feature.get('scraper_code') ?? ''
    const s = summaryMapRef.current[code]
    const avgStock = s ? s.total_stock_kg / Math.max(s.total_dealers, 1) : 0
    const fill = s ? stockColor(avgStock) : '#CBD5E1'

    return new Style({
      fill: new Fill({ color: isHovered ? fill + 'DD' : fill + '99' }),
      stroke: new Stroke({
        color: isHovered ? '#1B7A3D' : '#FFFFFF',
        width: isHovered ? 2.5 : 1,
      }),
      text: isHovered
        ? new Text({
            text: feature.get('name_ta') ?? feature.get('dtname') ?? '',
            font: 'bold 11px Inter, sans-serif',
            fill: new Fill({ color: '#1a1a1a' }),
            stroke: new Stroke({ color: '#fff', width: 3 }),
          })
        : undefined,
    })
  }

  useEffect(() => {
    if (!mapRef.current || olMap.current) return

    const source = new VectorSource({
      url: '/geo/tn-districts.geojson',
      format: new GeoJSON(),
    })

    const vLayer = new VectorLayer({
      source,
      style: (feature) => makeStyle(feature, false),
    })
    vectorLayer.current = vLayer

    const map = new Map({
      target: mapRef.current,
      layers: [
        new TileLayer({ source: new OSM() }),
        vLayer,
      ],
      view: new View({
        center: fromLonLat([78.66, 11.12]),
        zoom: 7,
      }),
    })
    olMap.current = map

    // Zoom to TN bounds once features load
    source.once('change', () => {
      if (source.getState() === 'ready' && source.getFeatures().length > 0) {
        const extent = createEmpty()
        source.getFeatures().forEach((f) => {
          const geom = f.getGeometry()
          if (geom) extend(extent, geom.getExtent())
        })
        map.getView().fit(extent, { padding: [30, 30, 30, 30], duration: 600 })
      }
    })

    // Hover highlight
    map.on('pointermove', (e) => {
      const feature = map.forEachFeatureAtPixel(e.pixel, (f) => f) ?? null
      const code: string = (feature?.get('scraper_code') as string) ?? null
      setHoveredCode(code)
      ;(map.getTargetElement() as HTMLElement).style.cursor = feature ? 'pointer' : ''
    })

    // Click → open info panel
    map.on('singleclick', (e) => {
      const feature = map.forEachFeatureAtPixel(e.pixel, (f) => f)
      if (!feature) { setPanel(null); return }
      const code: string = feature.get('scraper_code') ?? ''
      const name_ta: string = feature.get('name_ta') ?? ''
      const name_en: string = feature.get('dtname') ?? feature.get('dist') ?? ''
      setPanel({ name_ta, name_en, scraper_code: code, summary: summaryMapRef.current[code] ?? null })
      setDistrict(code)
    })

    return () => {
      map.setTarget(undefined)
      olMap.current = null
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // Re-style when summary data or hover changes
  useEffect(() => {
    if (!vectorLayer.current) return
    vectorLayer.current.setStyle((feature) =>
      makeStyle(feature, feature.get('scraper_code') === hoveredCode)
    )
  }, [summary, hoveredCode]) // eslint-disable-line react-hooks/exhaustive-deps

  // Update panel summary when data loads
  useEffect(() => {
    if (panel && summary) {
      const updated = summaryMapRef.current[panel.scraper_code] ?? null
      if (updated !== panel.summary) setPanel((p) => p ? { ...p, summary: updated } : p)
    }
  }, [summary]) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="flex gap-4" style={{ height: 'calc(100vh - 88px)' }}>
      {/* Map container */}
      <div className="flex-1 rounded-xl overflow-hidden shadow-sm border border-gray-200 relative">
        <div ref={mapRef} className="w-full h-full" />
        {/* Legend */}
        <div className="absolute bottom-4 left-4 bg-white/90 backdrop-blur-sm rounded-lg p-3 text-xs shadow-sm border border-gray-100">
          <p className="font-semibold text-gray-700 mb-2">Avg Stock / Dealer</p>
          {[
            { color: '#27AE60', label: 'Adequate (≥500 kg)' },
            { color: '#F1C40F', label: 'Caution (300–500 kg)' },
            { color: '#F39C12', label: 'Warning (100–300 kg)' },
            { color: '#E74C3C', label: 'Critical (<100 kg)' },
            { color: '#CBD5E1', label: 'No data' },
          ].map(({ color, label }) => (
            <div key={label} className="flex items-center gap-2 mb-1">
              <div className="w-3 h-3 rounded-sm shrink-0" style={{ background: color, opacity: 0.8 }} />
              <span className="text-gray-600">{label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Info Panel */}
      <div className="w-72 shrink-0">
        {panel ? (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 flex flex-col h-full overflow-y-auto">
            <div className="flex items-start justify-between p-4 border-b border-gray-100">
              <div>
                <p className="font-bold text-lg leading-tight">{panel.name_ta}</p>
                <p className="text-xs text-gray-400 mt-0.5">{panel.name_en}</p>
              </div>
              <button
                onClick={() => { setPanel(null); setDistrict(null) }}
                className="text-gray-300 hover:text-gray-600 text-2xl leading-none ml-2"
              >
                ×
              </button>
            </div>

            <div className="grid grid-cols-2 gap-3 p-4">
              <div className="bg-gray-50 rounded-lg p-3">
                <p className="text-xs text-gray-400">Dealers</p>
                <p className="text-2xl font-bold text-gray-900">{panel.summary?.total_dealers ?? '—'}</p>
              </div>
              <div className="bg-gray-50 rounded-lg p-3">
                <p className="text-xs text-gray-400">Total Stock</p>
                <p className="text-2xl font-bold text-gray-900">
                  {panel.summary ? `${(panel.summary.total_stock_kg / 1000).toFixed(1)}T` : '—'}
                </p>
              </div>
            </div>

            {panel.summary && (
              <div className="px-4 space-y-3">
                <div>
                  <p className="text-xs text-gray-400">Avg stock per dealer</p>
                  <p className="text-sm font-semibold" style={{ color: stockColor(panel.summary.total_stock_kg / Math.max(panel.summary.total_dealers, 1)) }}>
                    {Math.round(panel.summary.total_stock_kg / Math.max(panel.summary.total_dealers, 1)).toLocaleString()} kg
                  </p>
                </div>
                <div>
                  <p className="text-xs text-gray-400">Last scraped</p>
                  <p className="text-sm text-gray-600">{panel.summary.last_scraped ?? '—'}</p>
                </div>
              </div>
            )}

            <div className="p-4 mt-auto space-y-2 border-t border-gray-100">
              <button
                onClick={() => navigate(`/dealers?district=${panel.scraper_code}`)}
                className="w-full bg-[#1B7A3D] text-white text-sm py-2 rounded-lg hover:bg-[#145c2e] transition"
              >
                View Dealers →
              </button>
              <button
                onClick={() => navigate('/alerts')}
                className="w-full border border-gray-200 text-gray-600 text-sm py-2 rounded-lg hover:bg-gray-50 transition"
              >
                View Alerts
              </button>
              <button
                onClick={() => navigate(`/trends`)}
                className="w-full border border-gray-200 text-gray-600 text-sm py-2 rounded-lg hover:bg-gray-50 transition"
              >
                Stock Trends
              </button>
            </div>
          </div>
        ) : (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 text-center text-gray-400">
            <div className="text-4xl mb-3">🗺</div>
            <p className="text-sm font-medium text-gray-500">Click a district</p>
            <p className="text-xs mt-1">to see dealer count, stock totals, and drill-down links</p>
          </div>
        )}
      </div>
    </div>
  )
}
