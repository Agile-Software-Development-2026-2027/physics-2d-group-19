import { http , HttpResponse } from 'msw'

const healthHandler = http.get('/api/health',() => {
    return HttpResponse.json({status:200})
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
        { username : 'operator' , role : 'operator'},
        { status : 200 })
})

const createExperementHandler = http.post('/api/experiments' , async ({ request }) => {
    const body = await request.json()
    return HttpResponse.json(
        { id:'exp-49' , ...body },
        {status : 200})
})

const getExperementHandler = http.get('/api/experiments/:id' , ({params}) => {
    return HttpResponse.json(
        {   id : params.id ,
            exps : 49 , exp_type : 1 , ill : 14 , intensity : 180 , pix_arr : 1.041667 , 
            no_skip : 1 , ctr : 0 , fluo : 0 , lin : 0 , axis : 0, },
        {status : 200})
})

const defaultParamsHandler = http.get('/api/params/defaults' , () => {
    return HttpResponse.json(
        { // dati per ora messi cosi , ma da verificare dalla US3
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
                disc_radius: 350
            },
            limits: {
                // in seguito 
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
    createExperementHandler,
    getExperementHandler,
    defaultParamsHandler,
    runStatusHandler
]

