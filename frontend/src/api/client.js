// Empty by default: requests go to the same origin (Vite proxy in dev, reverse proxy in prod).
const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''

export async function apiFetch(path, options = {}) {
  const res = await fetch(`${BASE_URL}/api${path}`, options)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

export const getHealth = () => apiFetch('/health')
