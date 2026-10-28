import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ProtectedRoute } from './components/ProtectedRoute';
import {useEffect, useState} from "react";

// Per il momento non esistono le pag
import { LoginPage } from './pages/LoginPage';
import { ExperimentPage } from './pages/ExperimentPage';
import { ProcessingPage } from './pages/ProcessingPage';
import { ResultsPage } from './pages/ResultsPage';

export function App() {
    const [backendStatus, setBackendStatus] = useState('checking');

    useEffect(() => {
        fetch('/api/health', {})
            .then((res) => {
                if (res.ok) setBackendStatus('ok');
                else setBackendStatus('unreachable');
            })
            .catch(() => setBackendStatus('unreachable'));
    }, []);

    return (
        <BrowserRouter>
            {/* Indicatore dello stato del backend visibile in tutte le pagine (US-15)  (messo per il momento)*/}
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
    );
}

export default App;