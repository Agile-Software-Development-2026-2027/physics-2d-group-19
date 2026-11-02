import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { describe, it, expect, beforeEach } from 'vitest'
import { setToken } from '../api/client'
import { server } from '../mocks/server'
import { Header } from './Header'

function renderHeader(path) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Header>
        <span>Backend: ok</span>
      </Header>
      <Routes>
        <Route path="/login" element={<p>login page</p>} />
        <Route path="/elaborazione" element={<p>processing page</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('Header', () => {
  beforeEach(() => {
    sessionStorage.clear()
  })

  it('da loggato mostra il nome dell’utente e «Esci»', async () => {
    setToken('abc')
    renderHeader('/elaborazione')

    // il nome arriva dal mock MSW di /api/auth/me
    expect(await screen.findByText('operator')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /esci/i })).toBeInTheDocument()
  })

  it('senza token non mostra né il nome né «Esci»', () => {
    renderHeader('/login')

    expect(
      screen.queryByRole('button', { name: /esci/i }),
    ).not.toBeInTheDocument()
    expect(screen.queryByText('operator')).not.toBeInTheDocument()
  })

  it('mostra sempre il contenuto passato come children', () => {
    renderHeader('/login')

    expect(screen.getByText('Backend: ok')).toBeInTheDocument()
  })

  it('se /api/auth/me fallisce mostra «Esci» senza nome', async () => {
    server.use(
      http.get('/api/auth/me', () => HttpResponse.json({}, { status: 401 })),
    )
    setToken('abc')
    renderHeader('/elaborazione')

    expect(
      await screen.findByRole('button', { name: /esci/i }),
    ).toBeInTheDocument()
    expect(screen.queryByText('operator')).not.toBeInTheDocument()
  })

  it('premendo «Esci» porta al login e nasconde nome e pulsante', async () => {
    setToken('abc')
    const user = userEvent.setup()
    renderHeader('/elaborazione')

    await screen.findByText('operator')
    await user.click(screen.getByRole('button', { name: /esci/i }))

    expect(screen.getByText('login page')).toBeInTheDocument()
    expect(
      screen.queryByRole('button', { name: /esci/i }),
    ).not.toBeInTheDocument()
    expect(screen.queryByText('operator')).not.toBeInTheDocument()
  })
})
