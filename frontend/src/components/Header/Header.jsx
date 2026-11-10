import { useEffect, useState } from 'react'
import { useLocation } from 'react-router-dom'
import { getMe, getToken } from '../../api/client/client.js'
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

  const isBackendOk = backendStatus === 'ok'

  return (
    <header className="w-full bg-surface border-b border-border shadow-xs sticky top-0 z-50 mb-10">
      <div className="max-w-7xl mx-auto px-6 py-6 flex items-center justify-between relative">

        {/* Angolo Sinistro: Stato Backend */}
        <div className="flex items-center gap-2 text-xs font-medium text-text-muted bg-bg border border-border px-3 py-1.5 rounded-full shadow-2xs">
          <span
            className={`w-2.5 h-2.5 rounded-full transition-colors duration-300 ${
              isBackendOk
                ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.6)]'
                : 'bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.6)]'
            }`}
          />
          <span className="truncate">{children}</span>
        </div>

        {/* Centro: Titolo */}
        <div className="absolute left-1/2 -translate-x-1/2 text-center">
          <h1 className="text-4xl md:text-5xl font-sponge text-text">
            tAlgae<span className="text-alga">Lab</span>
          </h1>
        </div>

        {/* Angolo Destro: Username e Logout */}
        <div className="flex items-center gap-3">
          {isLoggedIn && (
            <>
              {username && (
                <span className="text-xs font-semibold text-text border border-border px-3 py-1.5 rounded-full">
                  {username}
                </span>
              )}
              <LogoutButton />
            </>
          )}
        </div>
      </div>
    </header>
  )
}