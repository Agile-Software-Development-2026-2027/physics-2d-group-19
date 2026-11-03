import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { http, HttpResponse, delay } from 'msw'
import { beforeEach, expect, test } from 'vitest'
import { server } from '../mocks/server'
import { LoginPage } from './LoginPage.jsx'

// The error message of the page for wrong credentials.
// Copy it exactly from LoginPage.jsx (the text inside setError)
const WRONG_CREDENTIALS_MESSAGE = 'Username or password incorrect'

// Start every test with an empty sessionStorage, so a token saved by one test
// does not change the result of the next one
beforeEach(() => {
  sessionStorage.clear()
})

// Show the login page inside a fake router.
// The fake "Processing page" is where the user must arrive after a correct login
function showLoginPage() {
  render(
    <MemoryRouter initialEntries={['/login']}>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/elaborazione" element={<div>Processing page</div>} />
      </Routes>
    </MemoryRouter>,
  )
}

// TEST 1
// The page must show the username field, the password field and the login button
test('shows the two fields and the button', () => {
  // Show the page
  showLoginPage()

  // Check that the three elements are on the screen
  expect(screen.getByLabelText('Username')).toBeInTheDocument()
  expect(screen.getByLabelText('Password')).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Login' })).toBeInTheDocument()
})

// TEST 2
// With correct credentials the user must go to the next page and the token must be saved
test('goes to the next page and saves the token with correct credentials', async () => {
  const user = userEvent.setup()
  showLoginPage()

  // Write the credentials accepted by the fake server and click the button
  await user.type(screen.getByLabelText('Username'), 'operator')
  await user.type(screen.getByLabelText('Password'), 'secret')
  await user.click(screen.getByRole('button', { name: 'Login' }))

  // Wait for the next page and check that the token was saved
  expect(await screen.findByText('Processing page')).toBeInTheDocument()
  expect(sessionStorage.getItem('token')).toBe('jwt_token')
})

// TEST 3
// With wrong credentials the page must show an error and must not save any token
test('shows an error with wrong credentials', async () => {
  const user = userEvent.setup()
  showLoginPage()

  // Write a wrong password and click the button
  await user.type(screen.getByLabelText('Username'), 'operator')
  await user.type(screen.getByLabelText('Password'), 'wrong')
  await user.click(screen.getByRole('button', { name: 'Login' }))

  // Wait for the error message and check that no token was saved
  expect(await screen.findByText(WRONG_CREDENTIALS_MESSAGE)).toBeInTheDocument()
  expect(sessionStorage.getItem('token')).toBeNull()
})

// TEST 4
// While the request is running the button must be disabled,
// so the user cannot click it twice
test('disables the button while the request is running', async () => {
  // Make the fake server slow (200 ms), so we have time to look at the button
  server.use(
    http.post('/api/auth/login', async () => {
      await delay(200)
      return HttpResponse.json({ token: 'jwt_token' })
    }),
  )
  const user = userEvent.setup()
  showLoginPage()

  // Write the credentials and click the button
  await user.type(screen.getByLabelText('Username'), 'operator')
  await user.type(screen.getByLabelText('Password'), 'secret')
  await user.click(screen.getByRole('button', { name: 'Login' }))

  // The server has not answered yet: the button must be disabled
  expect(screen.getByRole('button', { name: 'Login' })).toBeDisabled()

  // Wait until the request is finished, so the test ends cleanly
  expect(await screen.findByText('Processing page')).toBeInTheDocument()
})