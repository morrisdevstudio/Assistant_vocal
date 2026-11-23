// Android peut déplacer le viewport visible pour montrer le curseur, même
// quand le document ne défile pas. Suivre sa hauteur ET son décalage conserve
// l'ensemble du cadre de l'app (bandeau compris) au-dessus du clavier.
export function pinAppToViewport() {
  const viewport = window.visualViewport
  if (!viewport) return () => {}
  const style = document.documentElement.style
  let frame = 0

  function update() {
    frame = 0
    // Laisser le zoom d'accessibilité déplacer et agrandir la page normalement.
    if (!viewport || Math.abs(viewport.scale - 1) > 0.01 || viewport.height <= 0) return
    style.setProperty('--app-viewport-height', `${viewport.height}px`)
    style.setProperty('--app-viewport-top', `${Math.max(0, viewport.offsetTop)}px`)
  }

  function schedule() {
    if (!frame) frame = requestAnimationFrame(update)
  }

  update()
  viewport.addEventListener('resize', schedule)
  viewport.addEventListener('scroll', schedule)
  window.addEventListener('resize', schedule)
  window.addEventListener('pageshow', schedule)
  return () => {
    cancelAnimationFrame(frame)
    viewport.removeEventListener('resize', schedule)
    viewport.removeEventListener('scroll', schedule)
    window.removeEventListener('resize', schedule)
    window.removeEventListener('pageshow', schedule)
    style.removeProperty('--app-viewport-height')
    style.removeProperty('--app-viewport-top')
  }
}
