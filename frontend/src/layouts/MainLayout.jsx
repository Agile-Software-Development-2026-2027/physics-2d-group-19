import { Outlet } from 'react-router-dom'
import { Header } from '../components/Header/Header.jsx'

export function MainLayout({ backendStatus }) {
  const statusLabel =backendStatus === 'checking'
    ? 'Verifica...'
    : `Backend: ${backendStatus}`

  return (
    <div className="min-h-screen flex flex-col bg-bg text-text transition-colors duration-200">
      <Header backendStatus={backendStatus}>
        {statusLabel}
      </Header>

      <main className="flex-1 w-full mx-auto">
        <Outlet />
      </main>
    </div>
  )
}