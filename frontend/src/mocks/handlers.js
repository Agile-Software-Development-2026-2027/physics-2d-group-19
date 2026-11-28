// Provisional: align with backend/app/schemas once US-3 (3.2, 3.3) is merged

import { http , HttpResponse } from 'msw'

const healthHandler = http.get('/api/health',() => {
    return HttpResponse.json({status:'ok'})
})

const loginHandler  = http.post('/api/auth/login' , async ({ request }) => {
    const body = await request.json()
    if (body.username === 'operator' && body.password === 'secret')
        return HttpResponse.json({ token : 'jwt_token' })
    else
        return HttpResponse.json({ detail : 'Incorrect username or password' }, { status : 401 })
})

const getCurrentUserHandler = http.get('/api/auth/me' , () => {
    return HttpResponse.json(
        { username : 'operator'}
        )
})

const createExperimentHandler = http.post('/api/experiments' , async ({ request }) => {
    const body = await request.json()
    return HttpResponse.json(
        { id:'exp-49' , ...body }
        )
})

// Mock in-memory storage for registered experiments
let mockExperiments = [
  {
    exps: 49,
    exp_type: 1,
    ill: 14,
    intensity: 180,
    pix_arr: 1.041667,
    no_skip: true,
    ctr: 0,
    fluo: 0,
    lin: 0,
    axis: 0,
  },
]

// GET /api/experiments -> List all registered experiments
const listExperimentsHandler = http.get('/api/experiments', () => {
  return HttpResponse.json(mockExperiments)
})

// GET /api/experiments/:id -> Retrieve settings of a single experiment
const getExperimentHandler = http.get('/api/experiments/:id', ({ params }) => {
  const exp = mockExperiments.find((e) => e.exps === Number(params.id))
  if (!exp) {
    return HttpResponse.json({ detail: 'Experiment not found' }, { status: 404 })
  }
  return HttpResponse.json(exp)
})

// PUT /api/experiments/:id -> Save or update experiment settings
const saveExperimentHandler = http.put('/api/experiments/:id', async ({ params, request }) => {
  const body = await request.json()
  const expId = Number(params.id)

  // Enforce URL id and body exps match (same validation as backend)
  if (body.exps !== expId) {
    return HttpResponse.json(
      {
        detail: [
          {
            loc: ['body', 'exps'],
            msg: 'exps must match the experiment number in the URL',
            type: 'value_error',
          },
        ],
      },
      { status: 422 },
    )
  }

  // Update existing experiment or append newly created one
  const idx = mockExperiments.findIndex((e) => e.exps === expId)
  if (idx >= 0) {
    mockExperiments[idx] = body
  } else {
    mockExperiments.push(body)
    mockExperiments.sort((a, b) => a.exps - b.exps)
  }
  return HttpResponse.json(body)
})

const getDefaultParamsHandler = http.get('/api/params/defaults', () => {
    return HttpResponse.json({
        tracking: {
            channel: 2,
            background_subtraction: true,
            background_method: 'mean',
            diameter: 5,
            minmass: 180,
            invert: false,
            search_range: 10,
            adaptive_stop: 5,
            adaptive_step: 0.98,
            memory: null,
            filter_stubs: 0,
        },
        analysis: {
            diam: 10,
            dt: 0.1,
            particle_show: 5,
            disc_radius: 350,
            flux_cg_in: 1,
            flux_cg_out: 150,
            tumbling_threshold: 5.0,
            radial_map: false,
            nskip: 1,
        },
        filters: {
            lifetime_min: 0,
            threshold_dist: 0,
            threshold_dist_tot: 0,
            dist_step: 1,
            strict: true,
            only_inside: true,
            blinking_ratio: 0,
            blinking_tolerance: 0,
            long_track_min_snaps: 0,
        },
        limits: {
            tracking: {
                channel: { minimum: 0, description: 'Video channel index' },
                background_subtraction: { description: 'Subtract the video background' },
                background_method: {
                    enum: ['mean', 'median'],
                    description: 'Method used to estimate the video background',
                },
                diameter: { minimum: 3, description: 'Feature diameter in pixels; odd and at least 3' },
                minmass: { minimum: 0, description: 'Minimum integrated feature brightness' },
                invert: { description: 'Detect dark features on a bright background' },
                search_range: { minimum: 0, description: 'Maximum displacement between linked frames' },
                adaptive_stop: { minimum: 0, description: 'Minimum search range during adaptive linking' },
                adaptive_step: { minimum: 0, description: 'Adaptive linking search range multiplier' },
                memory: { minimum: 0, description: 'Missing frames allowed; null uses the video frame count minus one' },
                filter_stubs: { minimum: 0, description: 'Minimum observations per retained track' },
            },
            analysis: {
                diam: { minimum: 0, description: 'Diameter used to smooth the illumination field' },
                dt: { exclusiveMinimum: 0, description: 'Time interval between consecutive frames' },
                particle_show: { minimum: 1, description: 'Gradient and velocity frame spacing' },
                disc_radius: { minimum: 0, description: 'Disc radius for flux and particle counts' },
                flux_cg_in: { minimum: 1, description: 'Frame spacing for detecting disc crossings' },
                flux_cg_out: { minimum: 1, description: 'Frames per flux aggregation interval' },
                tumbling_threshold: { minimum: 0, description: 'Tumbling angular velocity threshold' },
                radial_map: { description: 'Use a radial energy density map' },
                nskip: { minimum: 1, description: 'Frame spacing for particle count statistics' },
            },
            filters: {
                lifetime_min: { minimum: 0, description: 'Minimum track lifetime' },
                threshold_dist: { minimum: 0, description: 'Minimum median step displacement' },
                threshold_dist_tot: { minimum: 0, description: 'Minimum track endpoint displacement' },
                dist_step: { minimum: 1, description: 'Observation spacing used by trajectory cleaning' },
                strict: { description: 'Apply strict trajectory endpoint filtering' },
                only_inside: { description: 'Keep only trajectory points inside the image' },
                blinking_ratio: { minimum: 0, description: 'Minimum track presence ratio' },
                blinking_tolerance: { minimum: 0, description: 'Long track presence ratio tolerance' },
                long_track_min_snaps: { minimum: 0, description: 'Observations required for long track tolerance' },
            },
        },
    })
})
    
const getRunStatusHandler = http.get('/api/runs/:id' , ({params}) => {
    if (params.id === 'run-queued')
        return HttpResponse.json(
            { id : params.id , status:'queued'  },
        )
    else if (params.id === 'run-tracking')
        return HttpResponse.json(
            { id : params.id , status:'running' },
        )
    else if (params.id === 'run-error')
        return HttpResponse.json(
            { id : params.id , status:'error' , message : 'An error occurred'}
            
        )
    else
        return HttpResponse.json(
            { id : params.id , status:'completed' , progress : 100 },
        )
})

const uploadIlluminationHandler = http.post('/api/experiments/:id/illumination' , ({params}) =>{
    return HttpResponse.json(
        {id:params.id , filename : 'illumination14.tiff'},
    )
})

const uploadVideoHandler = http.post('/api/videos' , () =>{
    return HttpResponse.json(
        {video_id : '0123456789ab', filename : 'tAlgae49.avi', size_bytes : 1800000000, frames : 1501, fps : 10},
        { status : 201 },
    )
})

// 1x1 grey PNG, enough for the <img> of DetectionPreview to show something.
const PREVIEW_PNG =
  'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAAAAAA6fptVAAAACklEQVR4nGNoAAAAggCBd81ytgAAAABJRU5ErkJggg=='

const getVideoPreviewHandler = http.get('/api/videos/:id/preview', ({ request }) => {
  const frame = Number(new URL(request.url).searchParams.get('frame') ?? 0)
  return HttpResponse.json({ frame, cell_count: 42, image: PREVIEW_PNG })
})

const startRunHandler = http.post('/api/runs', () => {
  return HttpResponse.json({ id: 'run-queued', status: 'queued' }, { status: 202 })
})


const listRunsHandler = http.get('/api/runs', () => {
  return HttpResponse.json([
    { id: 'run-completed', experiment_id: 'exp-49', status: 'completed', created_at: '2026-10-29T10:00:00' },
    { id: 'run-error', experiment_id: 'exp-49', status: 'error', created_at: '2026-10-28T09:30:00' },
  ])
})


// Same names as RESULT_NAMES in backend/app/services/results.py
const RESULT_NAMES = [
  'theta',
  'theta_y',
  'theta_y_axis0',
  'theta_y_axis1',
  'flux',
  'angle',
  'omega',
  'tumbling_orientation',
  'tumbling_duration',
  'nt_stats',
]

// GET /api/jobs/{job_id}/results -> list_results (backend/app/api/results.py)
const listResultsHandler = http.get('/api/jobs/:id/results', ({ params }) => {
  return HttpResponse.json(
    RESULT_NAMES.map((name) => ({
      name,
      url: `/api/jobs/${params.id}/results/${name}.csv`,
    })),
  )
})

// GET /api/jobs/{job_id}/results/{name}.csv -> get_result (backend/app/api/results.py)
const downloadResultCsvHandler = http.get('/api/jobs/:id/results/:name.csv', ({ params }) => {
  return new HttpResponse(`${params.name},dists,time\n0.29,794.83,4.4\n`, {
    headers: { 'Content-Type': 'text/csv' },
  })
})

// GET /api/jobs/{job_id}/config -> get_job_config (backend/app/api/jobs.py, 23.1)
const getJobConfigHandler = http.get('/api/jobs/:id/config', () => {
  return HttpResponse.json({
    version: 1,
    created_at: '2026-11-13T16:42:10.123456+00:00',
    experiment: {
      exps: 49, exp_type: 1, ill: 14, intensity: 180, pix_arr: 1.041667,
      no_skip: true, ctr: 0, fluo: 0, lin: 0, axis: 0,
    },
    params: {
      tracking: {
        channel: 2, background_subtraction: true, background_method: 'mean', diameter: 5,
        minmass: 180, invert: false, search_range: 10, adaptive_stop: 5, adaptive_step: 0.98,
        memory: null, filter_stubs: 0,
      },
      analysis: {
        diam: 10, dt: 0.1, particle_show: 5, disc_radius: 350, flux_cg_in: 1,
        flux_cg_out: 150, tumbling_threshold: 5.0, radial_map: false, nskip: 1,
      },
      filters: {
        lifetime_min: 0, threshold_dist: 0, threshold_dist_tot: 0, dist_step: 1, strict: true,
        only_inside: true, blinking_ratio: 0, blinking_tolerance: 0, long_track_min_snaps: 0,
      },
    },
    inputs: { video: 'tAlgae49.avi', illumination: 'illumination14.tiff' },
  })
})

// job_id -> how many times its status was read
const jobPolls = new Map()
let lastJob = 0

const createJobHandler = http.post('/api/jobs', () => {
  const jobId = String(++lastJob).padStart(12, '0')
  jobPolls.set(jobId, 0)
  return HttpResponse.json({ job_id: jobId, status: 'queued' }, { status: 202 })
})

const getJobHandler = http.get('/api/jobs/:id', ({ params }) => {
  if (!jobPolls.has(params.id))
    return HttpResponse.json({ detail: 'Job not found' }, { status: 404 })
  const polls = jobPolls.get(params.id)
  jobPolls.set(params.id, polls + 1)
  return HttpResponse.json({
    job_id: params.id,
    exp_id: 49,
    status: polls === 0 ? 'analysis' : 'done',
    error: null,
  })
})

const plotItems = (id) => [
  { name: 'theta_distribution', url: `/api/jobs/${id}/plots/theta_distribution.png`, error: null },
  { name: 'flux', url: null, error: 'boom' },
  { name: 'omega_distribution', url: `/api/jobs/${id}/plots/omega_distribution.png`, error: null },
]
// Cannot use id because MSW passes a params object to the function
const listPlotsHandler = http.get('/api/jobs/:id/plots', ({params}) => {
  return HttpResponse.json(plotItems(params.id))
})


const downloadPlotHandler = http.get('/api/jobs/:id/plots/:name.png', () =>{
  return new HttpResponse(new Uint8Array([137, 80, 78, 71]), {
      headers: {'Content-Type': 'image/png'},
    })
})


// Tiny valid images, so the GIF viewer shows something in development
const decodeBase64 = (text) => Uint8Array.from(atob(text), (c) => c.charCodeAt(0))
const ONE_PIXEL_GIF = decodeBase64('R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7')
const ONE_PIXEL_PNG = decodeBase64(
  'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=',
)

// GET /api/jobs/{job_id}/gif -> get_gif (backend/app/api/gif.py, 24.2)
const getGifHandler = http.get('/api/jobs/:id/gif', () => {
  return new HttpResponse(ONE_PIXEL_GIF, { headers: { 'Content-Type': 'image/gif' } })
})

// GET /api/jobs/{job_id}/gif/frames -> get_frames: same keys as frames.json (24.1)
const getGifFramesHandler = http.get('/api/jobs/:id/gif/frames', () => {
  return HttpResponse.json({
    count: 6,
    concentration: [1.0, 1.08, 1.21, 1.35, 1.42, 1.5],
    cells_in_ring: [12, 13, 15, 17, 18, 19],
    frame_indices: [0, 10, 20, 30, 40, 50],
  })
})

// GET /api/jobs/{job_id}/gif/frames/{i}.png -> get_frame
const getGifFrameHandler = http.get('/api/jobs/:id/gif/frames/:name.png', () => {
  return new HttpResponse(ONE_PIXEL_PNG, { headers: { 'Content-Type': 'image/png' } })
})

// POST /api/experiments/import -> Parse and import Clamidomoni_settings.txt
const importExperimentsHandler = http.post('/api/experiments/import', async ({ request }) => {
  const formData = await request.formData()
  const file = formData.get('file')
  if (!file) {
    return HttpResponse.json({ detail: 'Missing file' }, { status: 422 })
  }

  const text = await file.text()
  const lines = text.split(/\r?\n/)
  const parsedRows = []
  let skippedEmpty = 0

  for (let i = 0; i < lines.length; i++) {
    const trimmed = lines[i].trim()
    if (!trimmed) continue
    const parts = trimmed.split(/\s+/).map(Number)
    if (parts.length !== 10 || parts.some(Number.isNaN)) {
      return HttpResponse.json(
        { detail: `Line ${i + 1}: expected 10 numeric columns` },
        { status: 422 },
      )
    }
    if (parts.slice(1).every((v) => v === 0)) {
      skippedEmpty++
      continue
    }
    parsedRows.push({ line: i + 1, parts })
  }

  let created = 0
  let updated = 0
  const errors = []

  for (const { line, parts } of parsedRows) {
    const [exps, exp_type, ill, intensity, pix_arr, no_skip, ctr, fluo, lin, axis] = parts
    if (exps < 0 || exp_type < 0 || exp_type > 5 || pix_arr <= 0) {
      errors.push({ line, detail: 'Invalid experiment field values' })
      continue
    }
    const row = {
      exps,
      exp_type,
      ill,
      intensity,
      pix_arr,
      no_skip: Boolean(no_skip),
      ctr,
      fluo,
      lin: Boolean(lin),
      axis,
    }
    const idx = mockExperiments.findIndex((e) => e.exps === exps)
    if (idx >= 0) {
      mockExperiments[idx] = row
      updated++
    } else {
      mockExperiments.push(row)
      created++
    }
  }
  mockExperiments.sort((a, b) => a.exps - b.exps)

  return HttpResponse.json({
    created,
    updated,
    skipped_empty: skippedEmpty,
    errors,
  })
})

// GET /api/experiments/export -> Download Clamidomoni_settings.txt
const exportExperimentsHandler = http.get('/api/experiments/export', () => {
  const byId = new Map(mockExperiments.map((e) => [e.exps, e]))
  const maxId = mockExperiments.reduce((max, e) => Math.max(max, e.exps), 0)
  const lines = []

  for (let id = 0; id <= maxId; id++) {
    const e = byId.get(id)
    if (!e) {
      lines.push(`${id} 0 0 0 0.000000 1 0 0 0 0`)
    } else {
      lines.push(
        `${e.exps} ${e.exp_type} ${e.ill} ${e.intensity} ${Number(e.pix_arr).toFixed(6)} ` +
        `${e.no_skip ? 1 : 0} ${e.ctr} ${e.fluo} ${e.lin ? 1 : 0} ${e.axis}`,
      )
    }
  }

  return new HttpResponse(`${lines.join('\n')}\n`, {
    headers: {
      'Content-Type': 'text/plain',
      'Content-Disposition': 'attachment; filename="Clamidomoni_settings.txt"',
    },
  })
})


export const handlers = [
    healthHandler,
    loginHandler , 
    getCurrentUserHandler , 
    createExperimentHandler,
    listExperimentsHandler,
    exportExperimentsHandler,
    importExperimentsHandler,
    getExperimentHandler,
    saveExperimentHandler,
    getDefaultParamsHandler,
    getRunStatusHandler,
    uploadIlluminationHandler,
    uploadVideoHandler,
    getVideoPreviewHandler,
    startRunHandler,
    listRunsHandler,
    listResultsHandler,
    downloadResultCsvHandler,
    getJobConfigHandler,
    getGifHandler,
    getGifFramesHandler,
    getGifFrameHandler,
    listPlotsHandler,
    downloadPlotHandler,
    createJobHandler,
    getJobHandler,
]

