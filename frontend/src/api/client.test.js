import { afterEach, expect, it, vi } from 'vitest'
import { apiFetch, apiFetchRaw, clearToken, getToken, setToken } from './client.js'

afterEach(() => {
    clearToken()
    vi.restoreAllMocks()
})

it('sends the token', async () => {
    const spy = vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response('{}', { status: 200 }))
    setToken('abc')
    await apiFetch('/health')
    expect(spy.mock.calls[0][1].headers.Authorization).toBe('Bearer abc')
})

it('does not send a header without a token', async () => {
    const spy = vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response('{}', { status: 200 }))
    await apiFetch('/health')
    expect(spy.mock.calls[0][1].headers.Authorization).toBeUndefined()
})

it('clearToken removes it', async () => {
    setToken('abc')
    clearToken()
    expect(getToken()).toBeNull()
})

it('throws an error with the HTTP status', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response('{}', { status: 401 }))
    await expect(apiFetch('/health')).rejects.toMatchObject({ status: 401 })
})

it('apiFetchRaw returns the raw response', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response('png', { status: 200 }))
    const res = await apiFetchRaw('/health')
    expect(await res.text()).toBe('png')
})

it('apiFetch fails on a body that is not JSON', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response('png', { status: 200 }))
    await expect(apiFetch('/health')).rejects.toThrow()
})

it.each([400, 404, 500])('throws with status %i', async (status) => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response('{}', { status }))
    await expect(apiFetch('/health')).rejects.toMatchObject({ status })
})

it('keeps the caller headers', async () => {
    const spy = vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response('{}', { status: 200 }))
    setToken('abc')
    await apiFetch('/health', { headers: { 'Content-Type': 'application/json' } })

    const headers = spy.mock.calls[0][1].headers
    expect(headers.Authorization).toBe('Bearer abc')
    expect(headers['Content-Type']).toBe('application/json')
})