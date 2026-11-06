import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ProtectedRoute } from './components/ProtectedRoute/ProtectedRoute.jsx'
import { useEffect, useState } from 'react'
import { getHealth } from './api/client/client.js'

import { ExperimentPage } from './pages/ExperimentPage/ExperimentPage.jsx'
import { ResultsPage } from './pages/ResultsPage/ResultsPage.jsx'
import { LoginPage } from './pages/LoginPage/LoginPage.jsx'
import { ProcessingPage } from './pages/ProcessingPage/ProcessingPage.jsx'
import { Header } from './components/Header/Header.jsx'

export default function App() {
  const [backendStatus, setBackendStatus] = useState('checking')

  useEffect(() => {
    getHealth()
      .then(() => setBackendStatus('ok'))
      .catch(() => setBackendStatus('unreachable'))
  }, [])

  return (
    <BrowserRouter>
      <Header>
        <span>Backend: {backendStatus}</span>
      </Header>
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
          path="/risultati/:jobId"
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
