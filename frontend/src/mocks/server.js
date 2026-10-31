import { setupServer } from 'msw/node' // imports the msw function designed to intercept network calls in a Node.js environment
import { handlers } from './handlers'  // import the array containing the test answers from the handlers.js file

// creates an instance of the mock server by unpacking the array of handlers
export const server = setupServer(...handlers)