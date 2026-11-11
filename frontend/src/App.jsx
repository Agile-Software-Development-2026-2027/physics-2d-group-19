import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ProtectedRoute } from './components/ProtectedRoute/ProtectedRoute.jsx'
import { useEffect, useState } from 'react'
import { getHealth } from './api/client/client.js'

import { LoginPage } from './pages/LoginPage/LoginPage.jsx'
import { ProcessingPage } from './pages/ProcessingPage/ProcessingPage.jsx'
import { MainLayout } from './layouts/MainLayout.jsx'
import { ResultsPage } from './pages/ResultsPage/ResultsPage.jsx'

export default function App() {
  const [backendStatus, setBackendStatus] = useState('checking')

  useEffect(() => {
    getHealth()
      .then(() => setBackendStatus('ok'))
      .catch(() => setBackendStatus('unreachable'))
  }, [])

  return (
    <BrowserRouter>
      <Routes>
        <Route element={<MainLayout backendStatus={backendStatus} />}>
          <Route path="/login" element={<LoginPage />} />

          <Route element={<ProtectedRoute />}>
            <Route path="/processing" element={<ProcessingPage />} />
            <Route path="/risultati/:jobId" element={<ResultsPage />} />
          </Route>
        </Route>

        {/* Redirect di fallback all'unica pagina */}
        <Route path="*" element={<Navigate to="/processing" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
