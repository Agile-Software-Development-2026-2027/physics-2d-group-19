import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach , beforeAll , afterAll} from 'vitest'
import { server } from '../mocks/server'


beforeAll(() => server.listen()) // So I start MSW before running any tests
afterEach(() => {
    cleanup() 
    server.resetHandlers()}) // clear the override that the test added with server.use()
afterAll(() => server.close()) // switch off MSW at the end of the tests


