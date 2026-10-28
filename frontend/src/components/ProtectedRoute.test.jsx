import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { describe, it, expect, beforeEach } from 'vitest';
import { ProtectedRoute } from './ProtectedRoute';

describe('ProtectedRoute', () => {
    beforeEach(() => {
        sessionStorage.clear();
    });

    it('reindirizza a /login se il token non è presente', () => {
        render(
            <MemoryRouter initialEntries={['/elaborazione']}>
                <Routes>
                    <Route path="/login" element={<div>Pagina di Login</div>} />
                    <Route
                        path="/elaborazione"
                        element={
                            <ProtectedRoute>
                                <div>Contenuto Protetto</div>
                            </ProtectedRoute>
                        }
                    />
                </Routes>
            </MemoryRouter>
        );

        expect(screen.getByText('Pagina di Login')).toBeInTheDocument();
        expect(screen.queryByText('Contenuto Protetto')).not.toBeInTheDocument();
    });

    it('mostra il contenuto protetto se il token è presente', () => {
        sessionStorage.setItem('token', 'fake-jwt-token');

        render(
            <MemoryRouter initialEntries={['/elaborazione']}>
                <Routes>
                    <Route path="/login" element={<div>Pagina di Login</div>} />
                    <Route
                        path="/elaborazione"
                        element={
                            <ProtectedRoute>
                                <div>Contenuto Protetto</div>
                            </ProtectedRoute>
                        }
                    />
                </Routes>
            </MemoryRouter>
        );

        expect(screen.getByText('Contenuto Protetto')).toBeInTheDocument();
    });
});