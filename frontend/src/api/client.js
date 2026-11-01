const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''

export async function apiFetchRaw(path, options = {}) {
  const headers = { ...options.headers }
  const token = getToken()
  if( token ) headers.Authorization = `Bearer ${token}`

  const res = await fetch(`${BASE_URL}/api${path}`, { ...options, headers })

  if( !res.ok ) {
    const err = new Error(`HTTP ${res.status}`)
    err.status = res.status
    throw err
  }
  return res
}

export async function apiFetch(path, options = {}) {
  const res = await apiFetchRaw(path, options)
  return res.json()
}

export const getHealth = () => apiFetch('/health')
export const getToken = () => sessionStorage.getItem('token')
export const setToken = (token) => sessionStorage.setItem('token', token)
export const clearToken = () => sessionStorage.removeItem('token')