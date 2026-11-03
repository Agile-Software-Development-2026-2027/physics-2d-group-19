import { useNavigate } from 'react-router-dom'
import { clearToken } from '../../api/client.js'

export function LogoutButton() {
  const navigate = useNavigate()

  function handleClick() {
    clearToken()
    navigate('/login', { replace: true })
  }

  return (
    <button type="button" onClick={handleClick}>
      Esci
    </button>
  )
}
