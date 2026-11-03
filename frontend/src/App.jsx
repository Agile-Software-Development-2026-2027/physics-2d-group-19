import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ProtectedRoute } from './components/ProtectedRoute'
import { useEffect, useState } from 'react'
import { getHealth } from './api/client.js'

import { ExperimentPage } from './pages/ExperimentPage/ExperimentPage.jsx'
import { ResultsPage } from './pages/ResultsPage/ResultsPage.jsx'
import { LoginPage } from './pages/LoginPage/LoginPage.jsx'
import { ProcessingPage } from './pages/ProcessingPage/ProcessingPage.jsx'
import {MainLayout} from './layouts/MainLayout/MainLayout.jsx'

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
        {/* Rotta pubblica: Login senza Header/Layout */}
        <Route path="/login" element={<LoginPage />} />

        {/* Rotte protette avvolte nel MainLayout */}
        <Route
          element={
            <ProtectedRoute>
              <MainLayout backendStatus={backendStatus} />
            </ProtectedRoute>
          }
        >
          <Route path="/esperimento" element={<ExperimentPage />} />
          <Route path="/elaborazione" element={<ProcessingPage />} />
          <Route path="/risultati/:jobId" element={<ResultsPage />} />
        </Route>

        {/* Redirect predefinito */}
        <Route path="*" element={<Navigate to="/elaborazione" replace />} />
      </Routes>
    </BrowserRouter>
  )
}