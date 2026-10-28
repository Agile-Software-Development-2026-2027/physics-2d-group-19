import { Navigate, useLocation } from 'react-router-dom';
import { getToken } from '../api/client';

export function ProtectedRoute({ children }) {
    const token = getToken();
    const location = useLocation();

    // Se l'utente non ha un token valido, reindirizza al login salvando la pagina di provenienza
    if (!token) {
        return <Navigate to="/login" state={{ from: location }} replace />;
    }

    return children;
}