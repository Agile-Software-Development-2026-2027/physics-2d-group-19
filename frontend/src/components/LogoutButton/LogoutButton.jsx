import { useNavigate } from 'react-router-dom'
import { clearToken } from '../../api/client/client.js'

export function LogoutButton() {
  const navigate = useNavigate()

  function handleClick() {
    clearToken()
    navigate('/login', { replace: true })
  }

  return (
    <button
      type="button"
      onClick={handleClick}
      className="px-3.5 py-1.5 text-xs font-semibold rounded-full border border-border bg-bg text-text-muted hover:text-red-600 dark:hover:text-red-400 hover:border-red-500/40 hover:bg-red-500/10 transition-all duration-150 cursor-pointer shadow-2xs flex items-center gap-1.5"
    >
      <svg
        className="w-3.5 h-3.5"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth="2"
          d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
        />
      </svg>
      Esci
    </button>
  )
}