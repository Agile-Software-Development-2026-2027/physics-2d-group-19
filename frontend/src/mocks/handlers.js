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

const getExperimentHandler = http.get('/api/experiments/:id' , ({params}) => {
    return HttpResponse.json(
        {   id : params.id ,
            exps : 49 , exp_type : 1 , ill : 14 , intensity : 180 , pix_arr : 1.041667 , 
            no_skip : 1 , ctr : 0 , fluo : 0 , lin : 0 , axis : 0, }
        )
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
        {id : 'vid-49', filename : 'tAlgae49.avi' , size_mb : 1800 ,  time_sec : 120},
    )
})

const getVideoPreviewHandler = http.get('/api/videos/:id/preview' , ({params}) =>{
    return HttpResponse.json(
        {id:params.id , png : '' , cell_count : 42}
    )
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


const getRunResultsHandler = http.get('/api/runs/:id/results', () => {
  return HttpResponse.json({
    theta: { x: [0, 1, 2], y: [0.1, 0.2, 0.3] },
    flux: { x: [0, 1, 2], y: [5, 6, 7] },
    omega: { x: [0, 1, 2], y: [1, 2, 3] },
  })
})


const downloadResultCsvHandler = http.get('/api/runs/:id/results/:quantity.csv', () =>{
    return HttpResponse.json(
        {content : 'content'}
    )
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


export const handlers = [
    healthHandler,
    loginHandler , 
    getCurrentUserHandler , 
    createExperimentHandler,
    getExperimentHandler,
    getDefaultParamsHandler,
    getRunStatusHandler,
    uploadIlluminationHandler,
    uploadVideoHandler,
    getVideoPreviewHandler,
    startRunHandler,
    listRunsHandler,
    getRunResultsHandler,
    downloadResultCsvHandler,
    listPlotsHandler,
    downloadPlotHandler,
    createJobHandler,
    getJobHandler
]

