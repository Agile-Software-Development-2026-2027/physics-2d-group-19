import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

async function enableMocking(){
  if (import.meta.env.VITE_USE_MSW !== 'true') return 
  const {worker} = await import ('./mocks/browser.js')
  return worker.start({onUnhandledRequest : 'bypass'})
}

enableMocking().then(() => {
  const root = createRoot(document.getElementById('root'))
  root.render(
    <StrictMode>
      <App />
    </StrictMode>,
  )
})