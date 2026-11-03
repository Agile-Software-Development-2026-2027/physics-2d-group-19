import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { login } from '../../api/client.js'
import styles from './LoginPage.module.css'

export function LoginPage() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [sending, setSending] = useState(false)
  const navigate = useNavigate()

  async function handleSubmit(event) {
    // Do not reload the page
    event.preventDefault()
    setError('')
    setSending(true)

    try {
      // login() also saves the token
      await login(username, password)
      navigate('/elaborazione')
    } catch {
      setError('Username or password incorrect')
      setSending(false)
    }
  }

  return (
    <div className={styles.loginPage}>
      <form onSubmit={handleSubmit}>
        <h1>Login</h1>

        <div>
          <label>
            Username
            <input
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
          </label>
        </div>

        <div>
          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </label>
        </div>

        <p>{error}</p>

        <button type="submit" disabled={sending}>
          Login
        </button>
      </form>
    </div>
  )
}
