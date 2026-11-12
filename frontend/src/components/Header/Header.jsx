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
    <header className="w-full bg-surface border-b border-border shadow-xs sticky top-0 z-50 mb-6 sm:mb-10">
      <div className="max-w-7xl mx-auto px-4 py-3 sm:px-6 sm:py-4 lg:py-6 flex flex-wrap lg:flex-nowrap items-center justify-between gap-y-2.5 relative">

        {/* Titolo: */}
        <div className="w-full text-center order-first pb-2 border-b border-border/50 lg:border-none lg:pb-0 lg:w-auto lg:order-none lg:absolute lg:left-1/2 lg:-translate-x-1/2">
          <h1 className="font-faster text-text leading-none">
            <span className="font-sponge text-black text-3xl sm:text-4xl lg:text-5xl">
              Mov
            </span>
            <span className="text-alga font-sponge text-2xl sm:text-3xl lg:text-4xl">
              chlamydomonas
            </span>
          </h1>
        </div>

        {/* Angolo Sinistro: Stato Backend */}
        <div className="flex items-center gap-2 text-[11px] sm:text-xs font-medium text-text-muted bg-bg border border-border px-2.5 py-1 sm:px-3 sm:py-1.5 rounded-full shadow-2xs max-w-[170px] sm:max-w-none">
          <span
            className={`w-2 h-2 sm:w-2.5 sm:h-2.5 shrink-0 rounded-full transition-colors duration-300 ${
              isBackendOk
                ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.6)]'
                : 'bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.6)]'
            }`}
          />
          <span className="truncate">{children}</span>
        </div>

        {/* Angolo Destro: Username e Logout */}
        <div className="flex items-center gap-2 sm:gap-3 ml-auto lg:ml-0">
          {isLoggedIn && (
            <>
              {username && (
                <span className="inline-flex items-center gap-1.5 sm:gap-2 text-[11px] sm:text-xs font-semibold text-text border border-border px-2.5 py-1 sm:px-3 sm:py-1.5 rounded-full shadow-2xs">
                  <i className="fa-regular fa-user text-alga"></i>
                  <span className="max-w-[90px] sm:max-w-none truncate">{username}</span>
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