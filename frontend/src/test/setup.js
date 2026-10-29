import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach , beforeAll , afterAll} from 'vitest'
import { server } from '../mocks/server'

afterEach(cleanup)

beforeAll(() => server.listen()) // So I start MSW before running any tests
afterEach(() => server.resetHandlers()) // Clear the React DOM and reset the MSW mocks after each individual test
afterAll(() => server.close()) // switch off MSW at the end of the tests


