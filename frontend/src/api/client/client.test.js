import { afterEach, expect, it, vi } from 'vitest'
import {
  apiFetch,
  apiFetchRaw,
  clearToken,
  getToken,
  setToken,
  getExperiment,
  uploadIllumination,
  uploadVideo,
  createJob,
  getJob
} from './client.js'

afterEach(() => {
  clearToken()
  vi.restoreAllMocks()
  vi.unstubAllGlobals()
})

// Minimal XMLHttpRequest stand-in: send() reports progress and answers with status/body
function stubXhr(status, body) {
  const sent = {}
  class FakeXhr {
    constructor() {
      this.upload = {}
      this.headers = {}
    }
    open(method, url) {
      Object.assign(sent, { method, url })
    }
    setRequestHeader(name, value) {
      this.headers[name] = value
    }
    send(form) {
      Object.assign(sent, { form, headers: this.headers })
      this.upload.onprogress?.({ lengthComputable: true, loaded: 1, total: 2 })
      this.status = status
      this.responseText = JSON.stringify(body)
      this.onload()
    }
  }
  vi.stubGlobal('XMLHttpRequest', FakeXhr)
  return sent
}

it('uploadVideo sends the video as file with the token and reports progress', async () => {
  const result = { video_id: '0123456789ab', filename: 'a.avi', size_bytes: 5, frames: 30, fps: 10 }
  const sent = stubXhr(201, result)
  setToken('jwt')
  const progress = []
  expect(await uploadVideo(new File(['video'], 'a.avi'), (f) => progress.push(f))).toEqual(result)
  expect(sent.method).toBe('POST')
  expect(sent.url).toContain('/api/videos')
  expect([...sent.form.keys()]).toEqual(['file'])
  expect(sent.headers.Authorization).toBe('Bearer jwt')
  expect(progress).toEqual([0.5])
})

it('uploadVideo rejects with the HTTP status', async () => {
  stubXhr(413, { detail: 'The video exceeds the size limit' })
  await expect(uploadVideo(new File(['video'], 'a.avi'))).rejects.toMatchObject({ status: 413 })
})

it('uploadIllumination sends the image as file and returns the canonical name', async () => {
  const result = { ill: 14, filename: 'illumination14.tiff' }
  const spy = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
    new Response(JSON.stringify(result), { status: 201 }),
  )
  const image = new File(['image'], 'original.tif')
  expect(await uploadIllumination(49, image)).toEqual(result)
  const [url, options] = spy.mock.calls[0]
  expect(url).toContain('/api/experiments/49/illumination')
  expect(options.method).toBe('POST')
  expect([...options.body.keys()]).toEqual(['file'])
  expect(options.body.get('file')).toBe(image)
})

it('sends the token', async () => {
  const spy = vi
    .spyOn(globalThis, 'fetch')
    .mockResolvedValue(new Response('{}', { status: 200 }))
  setToken('abc')
  await apiFetch('/health')
  expect(spy.mock.calls[0][1].headers.Authorization).toBe('Bearer abc')
})

it('does not send a header without a token', async () => {
  const spy = vi
    .spyOn(globalThis, 'fetch')
    .mockResolvedValue(new Response('{}', { status: 200 }))
  await apiFetch('/health')
  expect(spy.mock.calls[0][1].headers.Authorization).toBeUndefined()
})

it('clearToken removes it', async () => {
  setToken('abc')
  clearToken()
  expect(getToken()).toBeNull()
})

it('throws an error with the HTTP status', async () => {
  vi.spyOn(globalThis, 'fetch').mockResolvedValue(
    new Response('{}', { status: 401 }),
  )
  await expect(apiFetch('/health')).rejects.toMatchObject({ status: 401 })
})

it('apiFetchRaw returns the raw response', async () => {
  vi.spyOn(globalThis, 'fetch').mockResolvedValue(
    new Response('png', { status: 200 }),
  )
  const res = await apiFetchRaw('/health')
  expect(await res.text()).toBe('png')
})

it('apiFetch fails on a body that is not JSON', async () => {
  vi.spyOn(globalThis, 'fetch').mockResolvedValue(
    new Response('png', { status: 200 }),
  )
  await expect(apiFetch('/health')).rejects.toThrow()
})

it.each([400, 404, 500])('throws with status %i', async (status) => {
  vi.spyOn(globalThis, 'fetch').mockResolvedValue(
    new Response('{}', { status }),
  )
  await expect(apiFetch('/health')).rejects.toMatchObject({ status })
})

it('keeps the caller headers', async () => {
  const spy = vi
    .spyOn(globalThis, 'fetch')
    .mockResolvedValue(new Response('{}', { status: 200 }))
  setToken('abc')
  await apiFetch('/health', { headers: { 'Content-Type': 'application/json' } })

  const headers = spy.mock.calls[0][1].headers
  expect(headers.Authorization).toBe('Bearer abc')
  expect(headers['Content-Type']).toBe('application/json')
})

it('getExperiment fetches experiment by ID without sending a body', async () => {
  const mockData = { id: 1, name: 'Test Experiment' }
  const spy = vi
    .spyOn(globalThis, 'fetch')
    .mockResolvedValue(new Response(JSON.stringify(mockData), { status: 200 }))

  const result = await getExperiment(1)

  expect(spy.mock.calls[0][0]).toContain('/experiments/1')
  expect(spy.mock.calls[0][1]?.body).toBeUndefined()
  expect(result).toEqual(mockData)
})

it('createJob sends the files to /jobs with POST', async () => {
  const spy = vi
    .spyOn(globalThis, 'fetch')
    .mockResolvedValue(new Response('{}', { status: 202 }))
  const formData = new FormData()
  formData.append('exp_id', '49')

  await createJob(formData)

  const [url, options] = spy.mock.calls[0]
  expect(url).toContain('/jobs')
  expect(options.method).toBe('POST')
  expect(options.body).toBe(formData)
})

it('getJob fetches the job status by ID', async () => {
  const spy = vi
    .spyOn(globalThis, 'fetch')
    .mockResolvedValue(new Response('{}', { status: 200 }))

  await getJob('abc')

  expect(spy.mock.calls[0][0]).toContain('/jobs/abc')
})

it('clears token and redirects to /login?expired=1 on 401 outside login', async () => {
  setToken('expired-jwt')
  const assignSpy = vi.fn()
  vi.stubGlobal('location', { assign: assignSpy })
  vi.spyOn(globalThis, 'fetch').mockResolvedValue(
    new Response('{}', { status: 401 }),
  )

  await expect(apiFetch('/jobs/abc')).rejects.toMatchObject({ status: 401 })

  expect(getToken()).toBeNull()
  expect(assignSpy).toHaveBeenCalledWith('/login?expired=1')
})

it('does not redirect on 401 from /auth/login', async () => {
  const assignSpy = vi.fn()
  vi.stubGlobal('location', { assign: assignSpy })
  vi.spyOn(globalThis, 'fetch').mockResolvedValue(
    new Response('{}', { status: 401 }),
  )

  await expect(apiFetch('/auth/login', { method: 'POST' })).rejects.toMatchObject({
    status: 401,
  })

  expect(assignSpy).not.toHaveBeenCalled()
})
