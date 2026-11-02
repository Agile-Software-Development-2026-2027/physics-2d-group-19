import { useEffect, useState } from 'react'
import { useLocation } from 'react-router-dom'
import { getMe, getToken } from '../api/client'
import { LogoutButton } from './LogoutButton'

export function Header({ children }) {
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

  return (
    <header className="site-header">
      <div className="header-status">{children}</div>
      {isLoggedIn && (
        <div className="header-actions">
          {username && <span>{username}</span>}
          <LogoutButton />
        </div>
      )}
    </header>
  )
}
