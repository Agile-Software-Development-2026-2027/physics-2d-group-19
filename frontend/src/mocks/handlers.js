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
        {status : 200})
    else
        return HttpResponse.json({detail : 'Incorrect username or password'},{status:401})
})

const meHandler = http.get('/api/auth/me' , () => {
    return HttpResponse.json(
        { username : 'operator'},
        { status : 200 })
})

const createExperimentHandler = http.post('/api/experiments' , async ({ request }) => {
    const body = await request.json()
    return HttpResponse.json(
        { id:'exp-49' , ...body },
        {status : 200})
})

const getExperimentHandler = http.get('/api/experiments/:id' , ({params}) => {
    return HttpResponse.json(
        {   id : params.id ,
            exps : 49 , exp_type : 1 , ill : 14 , intensity : 180 , pix_arr : 1.041667 , 
            no_skip : 1 , ctr : 0 , fluo : 0 , lin : 0 , axis : 0, },
        {status : 200})
})

const defaultParamsHandler = http.get('/api/params/defaults' , () => {
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
        {status : 200}
    )
})
    
const runStatusHandler = http.get('/api/runs/:id' , ({params}) => {
    return HttpResponse.json(
        { id : params.id , status:'completed' , progress : 100 },
        {status : 200}
    )
})



export const handlers = [
    healthHandler,
    loginHandler , 
    meHandler , 
    createExperimentHandler,
    getExperimentHandler,
    defaultParamsHandler,
    runStatusHandler
]

