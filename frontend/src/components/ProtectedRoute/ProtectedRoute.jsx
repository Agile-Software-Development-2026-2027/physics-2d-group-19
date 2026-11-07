import { Navigate, Outlet } from 'react-router-dom'
import { getToken } from '../../api/client/client.js'

export function ProtectedRoute({ children }) {
  const isLoggedIn = Boolean(getToken())

  if (!isLoggedIn) {
    return <Navigate to="/login" replace />
  }

  return children ? children : <Outlet />
}