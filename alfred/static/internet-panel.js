const el = id => document.getElementById(id);
const feedback = (text, error = false) => {
  el("internet-feedback").textContent = text;
  el("internet-feedback").classList.toggle("error", error);
};
async function api(path, body) {
  const response = await fetch(path, body === undefined ? {cache: "no-store"} : {
    method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(body)});
  const data = await response.json();
  if (!response.ok) throw new Error(typeof data.detail === "string" ? data.detail : "Réglages Internet indisponibles.");
  return data;
}
function display(value) {
  el("internet-state").textContent = value.configuration_error ? "Clé à vérifier" : value.access_verified ? "Accès vérifié" : value.configured ? "Clé configurée · accès à tester" : "Clé Tavily à configurer";
  el("internet-limit").value = value.credit_limit;
  el("internet-location").textContent = value.location ? `Commune : ${value.location.name}, ${value.location.admin1}, ${value.location.country}` : "Aucune commune enregistrée.";
  el("internet-usage").textContent = `${value.credits_used} / ${value.credit_limit} crédits réservés · mois UTC ${value.month}${value.quota_blocked ? " · quota fournisseur bloqué" : ""}`;
  el("internet-storage").textContent = `Clé protégée : ${value.storage}. Elle n’est jamais renvoyée au navigateur.`;
  el("internet-check").disabled = !value.configured || value.quota_blocked || value.credits_used >= value.credit_limit;
}
el("internet-location-form").addEventListener("submit", async event => {
  event.preventDefault();
  try {
    const data = await api("/api/internet/locations?q=" + encodeURIComponent(el("internet-city").value.trim()));
    const select = el("internet-locations"); select.replaceChildren(new Option("Conserver la commune actuelle", ""));
    for (const location of data.results) select.add(new Option(`${location.name}, ${location.admin1}, ${location.country}`, location.id));
    feedback(data.results.length ? "Choisissez la commune puis enregistrez." : "Aucune commune trouvée. Précisez la région ou le pays.");
  } catch (error) { feedback(error.message, true); }
});
el("internet-config-form").addEventListener("submit", async event => {
  event.preventDefault(); el("internet-save").disabled = true;
  const body = {credit_limit: Number(el("internet-limit").value), clear_location: el("internet-clear-location").checked};
  if (el("internet-locations").value && !body.clear_location) body.location_id = Number(el("internet-locations").value);
  const key = el("internet-key").value.trim(); if (key) body.api_key = key;
  el("internet-key").value = "";
  try {
    display(await api("/api/internet/config", body));
    el("internet-locations").value = ""; el("internet-clear-location").checked = false;
    feedback("Réglages enregistrés. La météo peut être demandée dans la conversation.");
  } catch (error) { feedback(error.message, true); }
  finally { el("internet-key").value = ""; el("internet-save").disabled = false; }
});
el("internet-check").addEventListener("click", async () => {
  el("internet-check").disabled = true; feedback("Vérification de la recherche…");
  try { display(await api("/api/internet/check", {})); feedback("Accès Tavily vérifié."); }
  catch (error) { feedback(error.message, true); }
  finally { try { display(await api("/api/internet/config")); } catch {} }
});
try { display(await api("/api/internet/config")); }
catch { feedback("Réglages Internet indisponibles. Rechargez la page après le démarrage du service.", true); }
window.addEventListener("hashchange", async () => {
  if (window.location.hash !== "#settings") return;
  try { display(await api("/api/internet/config")); } catch {}
});
