import { setupWorker } from 'msw/browser' // Import the specific function from MSW to handle the interception of network calls within the browser
import { handlers } from './handlers' // import the array containing the test answers from the handlers.js file

// I create the worker object by splitting the list of handlers, so that I can start the dummy server with `worker.start()`
export const worker = setupWorker(...handlers) 
