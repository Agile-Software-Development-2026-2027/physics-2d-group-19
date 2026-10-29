import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ProtectedRoute } from './components/ProtectedRoute'
import { useEffect, useState } from 'react'
import { getHealth } from './api/client.js'

import { ExperimentPage } from './pages/ExperimentPage.jsx'
import { ResultsPage } from './pages/ResultsPage.jsx'
import { LoginPage } from './pages/LoginPage.jsx'
import { ProcessingPage } from './pages/ProcessingPage.jsx'

export default function App() {
  const [backendStatus, setBackendStatus] = useState('checking')

  useEffect(() => {
    getHealth()
      .then(() => setBackendStatus('ok'))
      .catch(() => setBackendStatus('unreachable'))
  }, [])

  return (
    <BrowserRouter>
      <header style={{ padding: '8px', borderBottom: '1px solid #ccc' }}>
        <span>Backend: {backendStatus}</span>
      </header>
      <Routes>
        {/* Rotta pubblica */}
        <Route path="/login" element={<LoginPage />} />

        {/* Rotte protette (US-7.4) */}
        <Route
          path="/esperimento"
          element={
            <ProtectedRoute>
              <ExperimentPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/elaborazione"
          element={
            <ProtectedRoute>
              <ProcessingPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/risultati"
          element={
            <ProtectedRoute>
              <ResultsPage />
            </ProtectedRoute>
          }
        />

        {/* Redirect predefinito se la rotta non esiste */}
        <Route path="*" element={<Navigate to="/elaborazione" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
