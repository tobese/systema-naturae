import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { COLOR_REGISTRY } from './colorRegistry.ts'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App colorRegistry={COLOR_REGISTRY} />
  </StrictMode>,
)
