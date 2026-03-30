import { Routes, Route, Navigate } from 'react-router-dom'
import AppShell from './components/layout/AppShell'
import Overview from './pages/Overview'
import MapExplorer from './pages/MapExplorer'
import SupplyMatrix from './pages/SupplyMatrix'
import Trends from './pages/Trends'
import DeepDive from './pages/DeepDive'
import Dealers from './pages/Dealers'
import DealerDetail from './pages/DealerDetail'
import Alerts from './pages/Alerts'
import Intelligence from './pages/Intelligence'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<AppShell />}>
        <Route index element={<Navigate to="/overview" replace />} />
        <Route path="overview" element={<Overview />} />
        <Route path="map" element={<MapExplorer />} />
        <Route path="supply-matrix" element={<SupplyMatrix />} />
        <Route path="trends" element={<Trends />} />
        <Route path="deep-dive" element={<DeepDive />} />
        <Route path="dealers" element={<Dealers />} />
        <Route path="dealers/:dealerCode" element={<DealerDetail />} />
        <Route path="alerts" element={<Alerts />} />
        <Route path="intelligence" element={<Intelligence />} />
        <Route path="*" element={<Navigate to="/overview" replace />} />
      </Route>
    </Routes>
  )
}
