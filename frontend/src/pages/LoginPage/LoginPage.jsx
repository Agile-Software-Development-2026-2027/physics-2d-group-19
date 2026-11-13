import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { login } from '../../api/client/client.js'

export function LoginPage() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [sending, setSending] = useState(false)
  const navigate = useNavigate()

  async function handleSubmit(event) {
    // Evita il ricaricamento della pagina
    event.preventDefault()
    setError('')
    setSending(true)

    try {
      // login() salva anche il token
      await login(username, password)
      navigate('/processing')
    } catch {
      setError('Username or password incorrect')
      setSending(false)
    }
  }

  return (
    <div className="max-w-md mx-auto my-12 p-6 md:p-8 bg-surface border border-border rounded-2xl shadow-sm">
      <form onSubmit={handleSubmit} className="space-y-5">
        <h1 className="text-3xl font-bold text-text font-roboto tracking-wide border-b border-border pb-3 text-center">
          Login
        </h1>

        <div>
          <label className="flex flex-col gap-1.5 text-sm font-semibold text-text cursor-pointer">
            Username
            <input
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-4 py-2.5 rounded-xl border border-border bg-bg text-text font-normal focus:outline-none focus:ring-2 focus:ring-alga/50 focus:border-alga transition-all"
            />
          </label>
        </div>

        <div>
          <label className="flex flex-col gap-1.5 text-sm font-semibold text-text cursor-pointer">
            Password
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-2.5 rounded-xl border border-border bg-bg text-text font-normal focus:outline-none focus:ring-2 focus:ring-alga/50 focus:border-alga transition-all"
            />
          </label>
        </div>

        {error && (
          <p role="alert" className="p-3.5 rounded-xl bg-red-500/10 border border-red-500/20 text-red-600 dark:text-red-400 text-sm font-medium">
            {error}
          </p>
        )}

        <button
          type="submit"
          disabled={sending}
          className="w-full py-3 px-6 rounded-xl font-semibold text-white bg-alga hover:bg-alga-hover shadow-xs transition-all duration-150 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer flex items-center justify-center gap-2"
        >
          {sending && (
            <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
          )}
          Login
        </button>
      </form>
    </div>
  )
}