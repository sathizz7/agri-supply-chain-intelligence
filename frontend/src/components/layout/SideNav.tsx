import { NavLink } from 'react-router-dom'
import {
  HomeIcon, MapIcon, TableCellsIcon, ChartBarIcon,
  MagnifyingGlassIcon, UsersIcon, BellIcon, LightBulbIcon,
} from '@heroicons/react/24/outline'

const nav = [
  { to: '/overview', label: 'Overview', Icon: HomeIcon },
  { to: '/map', label: 'Map Explorer', Icon: MapIcon },
  { to: '/supply-matrix', label: 'Supply Matrix', Icon: TableCellsIcon },
  { to: '/trends', label: 'Trends', Icon: ChartBarIcon },
  { to: '/deep-dive', label: 'Deep-Dive', Icon: MagnifyingGlassIcon },
  { to: '/dealers', label: 'Dealers', Icon: UsersIcon },
  { to: '/alerts', label: 'Alerts', Icon: BellIcon },
  { to: '/intelligence', label: 'Intelligence', Icon: LightBulbIcon },
]

export default function SideNav() {
  return (
    <nav className="w-60 bg-[#1B7A3D] flex flex-col py-4 shrink-0">
      <div className="px-4 mb-6">
        <span className="text-white font-bold text-lg leading-tight">TFAIS</span>
        <p className="text-green-200 text-xs mt-0.5">Fertilizer Intelligence</p>
      </div>
      <ul className="flex-1 space-y-0.5 px-2">
        {nav.map(({ to, label, Icon }) => (
          <li key={to}>
            <NavLink
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                  isActive
                    ? 'bg-white/20 text-white font-medium'
                    : 'text-green-100 hover:bg-white/10 hover:text-white'
                }`
              }
            >
              <Icon className="w-5 h-5 shrink-0" />
              {label}
            </NavLink>
          </li>
        ))}
      </ul>
    </nav>
  )
}
