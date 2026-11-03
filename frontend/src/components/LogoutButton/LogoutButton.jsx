import { useNavigate } from 'react-router-dom'
import { clearToken } from '../../api/client.js'

export function LogoutButton() {
  const navigate = useNavigate()

  function handleClick() {
    clearToken()
    navigate('/login', { replace: true })
  }

  return (
    <button type="button" className="cursor-pointer hover:bg-gray-400" onClick={handleClick}>
      Esci
    </button>
  )
}
