import { Outlet } from 'react-router-dom'
import TopBar from './TopBar'
import SideNav from './SideNav'

export default function AppShell() {
  return (
    <div className="flex h-screen overflow-hidden bg-gray-50">
      <SideNav />
      <div className="flex flex-col flex-1 overflow-hidden">
        <TopBar />
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
