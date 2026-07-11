import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { COLOR_REGISTRY } from './colorRegistryUarchaea.ts'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App kingdom="archaea" colorRegistry={COLOR_REGISTRY} />
  </StrictMode>,
)
