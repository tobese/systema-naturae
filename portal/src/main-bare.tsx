import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import AppBare from './AppBare.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <AppBare />
  </StrictMode>,
)
