// Switch views without recreating controls or losing an ongoing test.
(() => {
  const views = [...document.querySelectorAll('[data-view]')];
  const links = [...document.querySelectorAll('[data-view-link]')];
  const content = document.getElementById('view-content');
  function showView(focus = false) {
    const requested = window.location.hash.slice(1);
    const current = views.find(view => view.dataset.view === requested) || views[0];
    for (const view of views) view.hidden = view !== current;
    for (const link of links) {
      if (link.dataset.viewLink === current.dataset.view) link.setAttribute('aria-current', 'page');
      else link.removeAttribute('aria-current');
    }
    if (focus) {
      content.focus({preventScroll: true});
      window.scrollTo({top: 0, behavior: 'instant'});
    }
  }
  window.addEventListener('hashchange', () => showView(true));
  showView();
})();
