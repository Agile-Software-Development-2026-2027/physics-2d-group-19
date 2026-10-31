const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''

export async function apiFetchRaw(path, options = {}) {
  const headers = { ...options.headers }
  const token = getToken()
  if (token) headers.Authorization = `Bearer ${token}`

  const res = await fetch(`${BASE_URL}/api${path}`, { ...options, headers })

  if (!res.ok) {
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

export async function login(username, password) {
  const data = await apiFetch(`/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ username, password }),
  })

  if (data.token) {
    setToken(data.token)
  }
  return data
}

export async function getUser() {
  return await apiFetch('/auth/me')
}

export async function logout() {
  clearToken()
}

export async function uploadExperimentSettings(settings) {
  const data = await apiFetch(`/experiments`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ settings: settings }),
  })

  return data
}

export async function getExperiment(id) {
  const data = await apiFetch(`/experiments/${id}`, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ id }),
  })
  return data
}

export async function uploadIllumination(id, imgFile) {
  const formData = new FormData()
  formData.append('img', imgFile)

  const data = await apiFetch(`/experiments/${id}/illumination`, {
    method: 'POST',
    body: formData,
  })

  return data
}

export async function uploadVideo(fileVideo) {
  const formData = new FormData()

  formData.append('video', fileVideo)

  const data = await apiFetch('/videos', {
    method: 'POST',
    body: formData,
  })

  return data.id
}

export async function getVideoPreview(id, frame = 0) {
  const res = await apiFetchRaw(`/videos/${id}/preview?frame=${frame}`)

  const imageBlob = await res.blob()
  const imageUrl = URL.createObjectURL(imageBlob)

  return imageUrl
}

export async function getDefaultParams() {
  return await apiFetch(`/params/defaults`)
}

export async function startExperiment(runConfig) {
  const data = await apiFetch(`/runs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(runConfig),
  })
  return data
}

export async function getExperimentStatus(id) {
  const data = await apiFetch(`/runs/${id}`, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
  })
  return data
}

export async function getElaborationResults(id) {
  return await apiFetch(`/runs/${id}/results`)
}

export async function downloadElaborationResultCsv(id, grandezza) {
  const res = await apiFetchRaw(`/runs/${id}/results/${grandezza}.csv`)

  const blob = await res.blob()

  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `${grandezza}_run_${id}.csv`
  document.body.appendChild(link)
  link.click()

  link.remove()
  URL.revokeObjectURL(url)
}

export async function getPlotsList(id) {
  return await apiFetch(`/runs/${id}/plots`)
}

export async function getPlotImageUrl(id, plotName) {
  const res = await apiFetchRaw(`/runs/${id}/plots/${plotName}.png`)

  const imageBlob = await res.blob()

  return URL.createObjectURL(imageBlob)
}

export async function getHystoryElaborations() {
  return await apiFetch(`/runs`)
}

export const getHealth = () => apiFetch('/health')
export const getToken = () => sessionStorage.getItem('token')
export const setToken = (token) => sessionStorage.setItem('token', token)
export const clearToken = () => sessionStorage.removeItem('token')
