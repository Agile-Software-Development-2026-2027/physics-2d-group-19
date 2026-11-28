const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''

export async function apiFetchRaw(path, options = {}) {
  const headers = { ...options.headers }
  const token = getToken()
  if (token) headers.Authorization = `Bearer ${token}`

  const res = await fetch(`${BASE_URL}/api${path}`, { ...options, headers })

  if (!res.ok) {
    if (res.status === 401 && path !== '/auth/login') {
      clearToken()
      window.location.assign('/login?expired=1')
    }
    const err = new Error(`HTTP ${res.status}`)
    err.status = res.status
    const body = await res.json().catch(() => null)
    if (body && typeof body === 'object') Object.assign(err, body)
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
  } else {
    throw new Error(
      data?.detail || 'Login failed: no token received from the server.',
    )
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

// GET /api/experiments -> list of recorded experiments
export async function getExperiments() {
  return await apiFetch('/experiments')
}

// GET /api/experiments/{id} -> details of a single experiment
export async function getExperiment(id) {
  return await apiFetch(`/experiments/${id}`)
}

// PUT /api/experiments/{id} -> save/update experiment settings
export async function saveExperiment(id, settings) {
  return await apiFetch(`/experiments/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(settings),
  })
}

export async function uploadIllumination(id, imgFile) {
  const formData = new FormData()
  formData.append('file', imgFile)

  const data = await apiFetch(`/experiments/${id}/illumination`, {
    method: 'POST',
    body: formData,
  })

  return data
}

// POST /api/videos -> {video_id, filename, size_bytes, frames, fps}
// fetch does not report upload progress, so this uses XMLHttpRequest;
// onProgress receives the fraction sent, from 0 to 1.
export function uploadVideo(fileVideo, onProgress) {
  const formData = new FormData()
  formData.append('file', fileVideo)

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest()
    xhr.open('POST', `${BASE_URL}/api/videos`)
    const token = getToken()
    if (token) xhr.setRequestHeader('Authorization', `Bearer ${token}`)

    xhr.upload.onprogress = (e) => {
      if (onProgress && e.lengthComputable) onProgress(e.loaded / e.total)
    }
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(JSON.parse(xhr.responseText))
        return
      }
      // Same handling as apiFetchRaw
      if (xhr.status === 401) {
        clearToken()
        window.location.assign('/login?expired=1')
      }
      const err = new Error(`HTTP ${xhr.status}`)
      err.status = xhr.status
      reject(err)
    }
    xhr.onerror = () => reject(new Error('Network error'))
    xhr.send(formData)
  })
}

export async function getVideoPreview(id, { frame = 0, diameter, minmass, background_method } = {}) {
  const query = new URLSearchParams({ frame })
  if (diameter !== undefined) query.set('diameter', diameter)
  if (minmass !== undefined) query.set('minmass', minmass)
  if (background_method) query.set('background_method', background_method)
  return apiFetch(`/videos/${id}/preview?${query}`)
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
  return await apiFetch(`/jobs/${id}/results`)
}

export async function downloadElaborationResultCsv(id, grandezza) {
  const res = await apiFetchRaw(`/jobs/${id}/results/${grandezza}.csv`)

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

// POST /api/jobs -> create_job
export async function createJob(formData) {
  return await apiFetch('/jobs', { method: 'POST', body: formData })
}
// GET /api/jobs/{job_id} -> get_job
export async function getJob(id) {
  return await apiFetch(`/jobs/${id}`)
}

// GET /api/jobs/{job_id}/config -> job_config (backend/app/api/jobs.py)
export async function getJobConfig(id) {
  return await apiFetch(`/jobs/${id}/config`)
}

// GET /api/jobs/{job_id}/plots/ -> list_plots (backend/app/api/plots.py)
export async function getPlotsList(id) {
  return await apiFetch(`/jobs/${id}/plots`)
}
// GET /api/jobs/{job_id}/plots/{filename}.png -> get_plot (backend/app/api/plots.py)
export async function getPlotImageUrl(id, plotName) {
  const res = await apiFetchRaw(`/jobs/${id}/plots/${plotName}.png`)

  const imageBlob = await res.blob()

  return URL.createObjectURL(imageBlob)
}

// GET /api/jobs/{job_id}/gif -> get_gif (backend/app/api/gif.py)
export async function getGifUrl(id) {
  const res = await apiFetchRaw(`/jobs/${id}/gif`)
  return URL.createObjectURL(await res.blob())
}

// GET /api/jobs/{job_id}/gif/frames -> get_frames: {count, concentration, cells_in_ring, frame_indices}
export async function getGifFrames(id) {
  return await apiFetch(`/jobs/${id}/gif/frames`)
}

// GET /api/jobs/{job_id}/gif/frames/{i}.png -> get_frame
export async function getGifFrameUrl(id, index) {
  const res = await apiFetchRaw(`/jobs/${id}/gif/frames/${index}.png`)
  return URL.createObjectURL(await res.blob())
}

export async function getHistoryElaborations() {
  return await apiFetch(`/runs`)
}

// POST /api/experiments/import -> bulk import from Clamidomoni_settings.txt
export async function importExperiments(file) {
  const formData = new FormData()
  formData.append('file', file)
  return await apiFetch('/experiments/import', {
    method: 'POST',
    body: formData,
  })
}

// GET /api/experiments/export -> download Clamidomoni_settings.txt
export async function exportExperiments() {
  const res = await apiFetchRaw('/experiments/export')
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = 'Clamidomoni_settings.txt'
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}

// POST /api/experiments/batch -> register multiple experiments with shared settings
export async function createExperimentsBatch(payload) {
  return await apiFetch('/experiments/batch', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export const getHealth = () => apiFetch('/health')
export const getMe = () => apiFetch('/auth/me')
export const getToken = () => sessionStorage.getItem('token')
export const setToken = (token) => sessionStorage.setItem('token', token)
export const clearToken = () => sessionStorage.removeItem('token')
