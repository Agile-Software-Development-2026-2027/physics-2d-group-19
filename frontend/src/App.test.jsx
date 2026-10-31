import { render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import App from './App.jsx'

afterEach(() => vi.unstubAllGlobals())

describe('App', () => {
  it('shows the backend status when the health check succeeds', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ status: 'ok' }),
      }),
    )
    render(<App />)
    expect(await screen.findByText('Backend: ok')).toBeInTheDocument()
    expect(fetch.mock.calls[0][0]).toBe('/api/health')
  })

  it('shows unreachable when the backend is down', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('down')))
    render(<App />)
    expect(await screen.findByText('Backend: unreachable')).toBeInTheDocument()
  })
})
