import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { http, HttpResponse } from 'msw'
import { afterEach, expect, test, vi } from 'vitest'
import { server } from '../../mocks/server.js'
import { ProcessingPage } from './ProcessingPage.jsx'

// Put back the real fetch after the tests that replace it with a spy
afterEach(() => {
  vi.restoreAllMocks()
})

// Show the page inside a fake router, with a fake results page.
// The status is read every 300 ms instead of 2 s, so the tests are fast
function showProcessingPage() {
  render(
    <MemoryRouter initialEntries={['/elaborazione']}>
      <Routes>
        <Route path="/elaborazione" element={<ProcessingPage pollMs={300} />} />
        <Route path="/risultati/:jobId" element={<div>Results page</div>} />
      </Routes>
    </MemoryRouter>,
  )
}

// Write the experiment number and choose the main file and the illumination image
async function chooseFiles(user, mainFile = 'tAlgae49.txt') {
  await user.type(screen.getByLabelText('Numero esperimento'), '49')
  await user.upload(
    screen.getByLabelText('Video o traiettorie'),
    new File(['x'], mainFile),
  )
  await user.upload(
    screen.getByLabelText('Illuminazione'),
    new File(['x'], 'illumination14.tiff'),
  )
}

// TEST 1
// The button must stay disabled until the number and both files are given
test('enables the button only when all the fields are filled', async () => {
  const user = userEvent.setup()
  showProcessingPage()
  const button = screen.getByRole('button', { name: 'Avvia' })

  expect(button).toBeDisabled()
  await user.type(screen.getByLabelText('Numero esperimento'), '49')
  await user.upload(
    screen.getByLabelText('Video o traiettorie'),
    new File(['x'], 'tAlgae49.txt'),
  )
  expect(button).toBeDisabled()
  await user.upload(
    screen.getByLabelText('Illuminazione'),
    new File(['x'], 'illumination14.tiff'),
  )
  expect(button).toBeEnabled()
})

// TEST 2
// The request must contain the experiment, the main file under the chosen name and the illumination
test('sends the experiment, the chosen file and the illumination', async () => {
  const spy = vi
    .spyOn(globalThis, 'fetch')
    .mockImplementation(async () =>
      Response.json({ job_id: 'abc', status: 'queued' }, { status: 202 }),
    )
  const user = userEvent.setup()
  showProcessingPage()

  // Choose "Video", so the main file must be an .avi sent as "video"
  await user.click(screen.getByLabelText('Video'))
  await chooseFiles(user, 'tAlgae49.avi')
  await user.click(screen.getByRole('button', { name: 'Avvia' }))

  expect(screen.getByText('In coda')).toBeInTheDocument()
  const [url, options] = spy.mock.calls[0]
  expect(url).toContain('/jobs')
  expect(options.body.get('exp_id')).toBe('49')
  expect(options.body.get('video').name).toBe('tAlgae49.avi')
  expect(options.body.get('illumination').name).toBe('illumination14.tiff')
})

// TEST 3
// The page must show the phase and open the results when the job is done
test('shows the phase and opens the results when the job is done', async () => {
  const user = userEvent.setup()
  showProcessingPage()

  await chooseFiles(user)
  await user.click(screen.getByRole('button', { name: 'Avvia' }))

  expect(await screen.findByText('Analisi')).toBeInTheDocument()
  expect(await screen.findByText('Results page')).toBeInTheDocument()
})

// TEST 4
// When the job fails the page must show its message and allow a new start
test('shows the error of a failed job', async () => {
  server.use(
    http.get('/api/jobs/:id', ({ params }) =>
      HttpResponse.json({
        job_id: params.id,
        exp_id: 49,
        status: 'error',
        error: 'No trajectories to analyse',
      }),
    ),
  )
  const user = userEvent.setup()
  showProcessingPage()

  await chooseFiles(user)
  await user.click(screen.getByRole('button', { name: 'Avvia' }))

  expect(await screen.findByText('No trajectories to analyse')).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Avvia' })).toBeEnabled()
})

// TEST 5
// Changing the kind keeps the file but checks it again
test('keeps the file and checks it again when the kind changes', async () => {
  const user = userEvent.setup()
  showProcessingPage()

  await chooseFiles(user)
  const button = screen.getByRole('button', { name: 'Avvia' })
  expect(button).toBeEnabled()

  // A .txt file is not a video
  await user.click(screen.getByLabelText('Video'))
  expect(screen.getByText('Il file deve essere .avi')).toBeInTheDocument()
  expect(button).toBeDisabled()

  // Back to trajectories: the same file is valid again
  await user.click(screen.getByLabelText('Traiettorie'))
  expect(screen.queryByText('Il file deve essere .avi')).not.toBeInTheDocument()
  expect(button).toBeEnabled()
})