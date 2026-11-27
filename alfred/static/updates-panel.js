const panel = document.getElementById('updates-panel');
const field = document.getElementById('updates-key');
const versions = document.getElementById('updates-versions');
const feedback = document.getElementById('updates-feedback');
const controls = document.getElementById('updates-controls');
const auto = document.getElementById('updates-auto');
const buttons = [...panel.querySelectorAll('[data-update]')];
let status;
let sending = false;
let polling = false;
let error = '';

function render() {
  const available = status?.available;
  controls.hidden = !available;
  if (status) {
    versions.textContent = available
      ? `Installée : ${status.installed || '—'} · Candidate : ${status.candidate || '—'}`
      : 'Disponible avec le paquet Debian alfred-home.';
    auto.checked = Boolean(status.auto_enabled);
  }
  const disabled = sending || !available || !window.isSecureContext || !field.value.trim()
    || ['queued', 'running'].includes(status.phase);
  for (const button of [...buttons, auto]) button.disabled = disabled;
  const message = error || (available && !window.isSecureContext ? 'Ouvrez Alfred en HTTPS pour effectuer une opération.' : status?.message) || '';
  if (feedback.textContent !== message) feedback.textContent = message;
}

async function refresh() {
  if (polling) return;
  polling = true;
  try {
    const result = await fetch('/api/updates', { cache: 'no-store' });
    if (!result.ok) throw new Error();
    status = await result.json();
  } catch {
    status = undefined;
    versions.textContent = 'Alfred est indisponible.';
  } finally {
    polling = false;
    render();
  }
}

async function request(operation) {
  if (sending) return;
  sending = true;
  error = '';
  render();
  try {
    const result = await fetch(`/api/updates/${operation}`, {
      method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Alfred-Update-Key': field.value.trim() }, body: '{}',
    });
    if (!result.ok) throw new Error((await result.json()).detail || 'Opération refusée.');
  } catch (problem) {
    error = problem instanceof TypeError ? 'Connexion au serveur Alfred interrompue.' : problem.message;
  } finally {
    sending = false;
    await refresh();
  }
}

field.addEventListener('input', () => { error = ''; render(); });
auto.addEventListener('change', () => request(auto.checked ? 'auto-on' : 'auto-off'));
for (const button of buttons) button.addEventListener('click', () => {
  const operation = button.dataset.update;
  if (operation === 'check' || window.confirm('Installer maintenant la dernière version disponible ? Alfred pourra redémarrer.')) {
    request(operation);
  }
});
panel.addEventListener('toggle', () => {
  if (panel.open) refresh();
  else { field.value = ''; error = ''; render(); }
});
window.addEventListener('hashchange', () => {
  if (location.hash === '#settings' && panel.open) refresh();
  else { field.value = ''; error = ''; render(); }
});
setInterval(() => { if (panel.open && !document.hidden && location.hash === '#settings' && !sending) refresh(); }, 2000);
