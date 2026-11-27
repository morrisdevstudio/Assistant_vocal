import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { App } from './App'
import './styles.css'
import { registerSW } from 'virtual:pwa-register'
import { pinAppToViewport } from './viewport'
import { applyAppearance, loadPreferences } from './preferences'

applyAppearance(loadPreferences().preferences)

const unpinViewport = pinAppToViewport()
if (import.meta.hot) import.meta.hot.dispose(unpinViewport)

registerSW({
  immediate: true,
  onRegisterError() { window.dispatchEvent(new Event('alfred-pwa-registration-error')) },
})

// Après une reconstruction, un nouveau service worker prend la main : recharger
// une fois évite de garder un index dont les assets fingerprintés n'existent plus.
if ('serviceWorker' in navigator) {
  const hadController = !!navigator.serviceWorker.controller
  let reloading = false
  navigator.serviceWorker.addEventListener('controllerchange', () => {
    if (!hadController || reloading) return
    reloading = true
    location.reload()
  })
}

createRoot(document.getElementById('root')!).render(
  <StrictMode><App /></StrictMode>,
)
