import { useEffect, useState } from 'react'
import { getHealth } from './api/client.js'

function App() {
  const [status, setStatus] = useState('checking...')

  useEffect(() => {
    getHealth()
      .then((data) => setStatus(data.status))
      .catch(() => setStatus('unreachable'))
  }, [])

  return (
    <main>
      <h1>Moving Chlamydomonas</h1>
      <p>Backend: {status}</p>
    </main>
  )
}

export default App
