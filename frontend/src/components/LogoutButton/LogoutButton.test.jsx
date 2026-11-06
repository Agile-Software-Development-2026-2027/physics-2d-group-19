import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { describe, it, expect, beforeEach } from 'vitest'
import { getToken, setToken } from '../../api/client/client.js'
import { LogoutButton } from './LogoutButton.jsx'

describe('LogoutButton', () => {
  beforeEach(() => {
    sessionStorage.clear()
  })

  it('cancella il token e porta al login', async () => {
    setToken('abc')
    const user = userEvent.setup()

    render(
      <MemoryRouter initialEntries={['/']}>
        <Routes>
          <Route path="/" element={<LogoutButton />} />
          <Route path="/login" element={<p>login page</p>} />
        </Routes>
      </MemoryRouter>,
    )

    await user.click(screen.getByRole('button', { name: /esci/i }))

    expect(getToken()).toBeNull()
    expect(screen.getByText('login page')).toBeInTheDocument()
  })
})
