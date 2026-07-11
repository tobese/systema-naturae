import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import AppBare from './AppBare.tsx'
import { COLOR_REGISTRY } from './colorRegistryUarchaea.ts'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <AppBare kingdom="archaea" colorRegistry={COLOR_REGISTRY} />
  </StrictMode>,
)
