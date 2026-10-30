import { http, HttpResponse } from 'msw'

export const sessionExpiredHandler = http.get('/api/auth/me', () => {
  return HttpResponse.json({ detail: 'Session expired' }, { status: 401 })
})

export const invalidVideoHandler = http.post('/api/videos', () => {
  return HttpResponse.json({ detail: 'Invalid video' }, { status: 400 })
})

export const runNotFoundHandler = http.get('/api/runs/:id', () => {
  return HttpResponse.json({ detail: 'Run not found' }, { status: 404 })
})

export const errorHandlers = [
  sessionExpiredHandler,
  invalidVideoHandler,
  runNotFoundHandler,
]