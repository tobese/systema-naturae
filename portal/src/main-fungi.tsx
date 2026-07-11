import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { COLOR_REGISTRY } from './colorRegistryFungi.ts'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App kingdom="fungi" colorRegistry={COLOR_REGISTRY} />
  </StrictMode>,
)