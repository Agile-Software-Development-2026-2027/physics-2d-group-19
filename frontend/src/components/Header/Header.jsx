import { useEffect, useState } from 'react'
import { useLocation, NavLink } from 'react-router-dom'
import { getMe, getToken } from '../../api/client.js'
import { LogoutButton } from '../LogoutButton/LogoutButton.jsx'

export function Header({ children, backendStatus }) {
  const location = useLocation()
  const isLoggedIn = Boolean(getToken())
  const [username, setUsername] = useState(null)

  useEffect(() => {
    if (!isLoggedIn) {
      return
    }
    getMe()
      .then((data) => setUsername(data.username))
      .catch(() => setUsername(null))
  }, [isLoggedIn, location.pathname])

  const navTabs = [
    { path: '/esperimento', label: 'Esperimento' },
    { path: '/elaborazione', label: 'Elaborazione' },
    { path: '/risultati', label: 'Risultati' },
  ]

  const isBackendOk = backendStatus === 'ok'

  return (
    <header className="w-full bg-header rounded-4xl pt-6 shadow-lg overflow-hidden">
      {/* Sezione Superiore: Allineamento orizzontale per Desktop */}
      <div className="w-full px-8 relative flex items-center justify-center py-4">

        {/* Angolo Sinistro: Stato Backend con pallino verde/rosso */}
        <div className="absolute left-8 flex items-center gap-2 text-xs font-medium text-slate-700 bg-slate-200/70 border border-slate-300/50 px-3.5 py-1.5 rounded-full shadow-xs">
          <span
            className={`w-2.5 h-2.5 rounded-full transition-colors duration-300 ${
              isBackendOk
                ? 'bg-emerald-500 shadow-[0_0_6px_rgba(16,185,129,0.5)]'
                : 'bg-red-500 shadow-[0_0_6px_rgba(239,68,68,0.5)]'
            }`}
          />
          {children}
        </div>

        {/* Centro: Titolo Principale */}
        <div className="text-center">
          <h1 className="text-6xl tracking-tight font-sponge">
            tAlgae<span className="text-secondary">Lab</span>
          </h1>
        </div>

        {/* Angolo Destro: Username e Tasto Esci */}
        {isLoggedIn && (
          <div className="absolute right-8 flex items-center gap-3 text-sm">
            {username && (
              <span className="font-semibold text-slate-700 bg-white border border-slate-200 px-3.5 py-1.5 rounded-full shadow-xs">
                👤 {username}
              </span>
            )}
            <LogoutButton />
          </div>
        )}
      </div>

      {/* Linea Divisoria Sottile */}
      <div className="w-full border-b border-black/10 mt-2 mb-2"></div>

      {/* Sezione Inferiore: Tab Navbar */}
      {isLoggedIn && (
        <nav className="flex justify-center items-end gap-1.5 px-4 max-w-3xl mx-auto font-young">
          {navTabs.map((tab) => (
            <NavLink
              key={tab.path}
              to={tab.path}
              className={({ isActive }) =>
                `px-5 py-2 text-sm font-medium transition-all duration-150 rounded-t-xl flex items-center gap-2 border-t border-x ${
                  isActive
                    ? 'bg-primary text-secondary font-semibold border-slate-300 border-t-2 border-t-secondary shadow-xs -mb-[1px] relative z-10'
                    : 'text-slate-600 hover:bg-slate-200/60 hover:text-slate-900 border-transparent'
                }`
              }
            >
              {tab.label}
            </NavLink>
          ))}
        </nav>
      )}
    </header>
  )
}