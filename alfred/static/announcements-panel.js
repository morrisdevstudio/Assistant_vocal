const el = id => document.getElementById(id);
el("announcement-scope").addEventListener("change", () => {
  const scope = el("announcement-scope").value;
  el("announcement-floor-field").hidden = scope !== "floor";
  el("announcement-room-field").hidden = scope !== "room";
  el("announcement-room").required = scope === "room";
});
el("announcement-form").addEventListener("submit", async event => {
  event.preventDefault();
  const button = event.submitter, feedback = el("announcement-feedback");
  const scope = el("announcement-scope").value;
  const body = {message:el("announcement-message").value.trim(), scope};
  if (scope === "floor") body.target = el("announcement-floor").value;
  if (scope === "room") body.target = el("announcement-room").value.trim();
  button.disabled = true; feedback.textContent = "Demande en cours…";
  try {
    const response = await fetch("/api/announcements", {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});
    const result = await response.json();
    if (!response.ok) throw new Error(typeof result.detail === "string" ? result.detail : "Annonce impossible.");
    feedback.textContent = result.message;
  } catch(error) { feedback.textContent = error.message; }
  finally { button.disabled = false; }
});
