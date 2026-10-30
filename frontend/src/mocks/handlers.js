// Provisional: align with backend/app/schemas once US-3 (3.2, 3.3) is merged

import { http , HttpResponse } from 'msw'

const healthHandler = http.get('/api/health',() => {
    return HttpResponse.json({status:'ok'})
})

const loginHandler  = http.post('/api/auth/login' , async ({ request }) => {
    const body = await request.json()
    if (body.username === 'operator' && body.password === 'secret')
        return HttpResponse.json(
        {access_token : 'jwt_token' , token_type : 'bearer'},
        )
    else
        return HttpResponse.json({detail : 'Incorrect username or password'},{status:401})
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

const getDefaultParamsHandler = http.get('/api/params/defaults' , () => {
    return HttpResponse.json(
        { 
            tracking: {
                diameter: 5,
                minmass: 180,
                search_range: 10,
                background_method: 'mean'
            },
            analysis: {
                scradius: 130,
                thickness: 0,
                radial_map: false,
                dt: 0.1,
                tumbling_threshold: 5.0,
                diam: 10,
                disc_radius: 130,
                lifetime_min:0,
                threshold_dist:1,
                threshold_dist_tot:3,
                blinking_ratio:0.5,
                color:2
            },
            limits: {
                
            }
        },
    )
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
            { id : params.id , status:'error' , messagge : 'An error occured'}
            
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

const plotNames = ['theta', 'flux', 'angle', 'omega', 'nt', 'tumbling', 'density']

const listPlotsHandler = http.get('/api/runs/:id/plots', () => {
  return HttpResponse.json(plotNames)
})


const downloadPlotHandler = http.get('/api/runs/:id/plots/:name.png', () =>{
    return HttpResponse.json(
        {content : 'content'}
    )
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
]

