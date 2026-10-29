import { http , HttpResponse } from 'msw'


const loginHandler  = http.post('/api/auth/login' , async ({ request }) => {
    const body = await request.json()
    if (body.username === 'operator' && body.password === 'secret')
        return HttpResponse.json(
        {access_token : 'jwt_token' , token_type : 'bearer'},
        {status : 200})
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

const getExperementHandler = http.get('/api/experiments/:id' , () => {
    return HttpResponse.json(
        { id: params.id , exps : 49 , exp_type : 1 , ill : 14 , intensity : 180 },
        {status : 200})
})

const defaultParamsHandler = http.get('/api/params/defaults' , () => {
    return HttpResponse.json(
        { 
            diameter:11,
            minmass:100,
            scradius:130,
            thickness:0,
            tumbling_threshold:5.0
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
    loginHandler , 
    meHandler , 
    createExperementHandler,
    getExperementHandler,
    defaultParamsHandler,
    runStatusHandler
]

