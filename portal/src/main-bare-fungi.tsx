import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import AppBare from './AppBare.tsx'
import { COLOR_REGISTRY } from './colorRegistryFungi.ts'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <AppBare kingdom="fungi" colorRegistry={COLOR_REGISTRY} />
  </StrictMode>,
)