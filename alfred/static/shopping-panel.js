const el = id => document.getElementById(id);
async function api(path, body) {
  const response = await fetch(path, body === undefined ? {} : {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(body)});
  const data = await response.json();
  if (!response.ok) throw new Error(typeof data.detail === "string" ? data.detail : "Demande impossible.");
  return data;
}
function feedback(text) { el("shopping-feedback").textContent = text; }
async function refresh() {
  const result = await api("/api/shopping/items");
  const completed = await api("/api/shopping/items/completed");
  async function action(path, payload) {
    const outcome=await api(path, payload);
    try { await refresh(); feedback(outcome.message); }
    catch(error) { feedback(outcome.message + " Lecture de la liste impossible : " + error.message); }
  }
  function makeButton(label, item, fn) {
    const button=document.createElement("button"); button.type="button"; button.className="secondary";
    button.textContent=label; button.setAttribute("aria-label", label + " " + item);
    button.addEventListener("click", async () => { button.disabled=true; try { await fn(); } catch(error) { feedback(error.message); } finally { button.disabled=false; } });
    return button;
  }
  function deleteButton(item) {
    return makeButton("Supprimer définitivement", item, async () => {
      if (window.confirm(`Supprimer définitivement « ${item} » de Home Assistant ?`))
        await action("/api/shopping/items/delete", {item,confirm_delete:true});
    });
  }
  el("shopping-items").replaceChildren(...result.items.map(item => {
    const li=document.createElement("li");
    const label=document.createElement("span"); label.textContent=item + " ";
    const button=document.createElement("button"); button.type="button"; button.className="secondary";
    button.textContent="Cocher"; button.setAttribute("aria-label", "Cocher " + item);
    button.addEventListener("click", async () => {
      button.disabled=true;
      try { const result=await api("/api/shopping/items/complete", {item}); try { await refresh(); feedback(result.message); } catch(error) { feedback(result.message + " Lecture de la liste impossible : " + error.message); } }
      catch(error) { feedback(error.message); button.disabled=false; }
    });
    const rename=makeButton("Modifier", item, async () => {
      const newName=window.prompt("Nouveau nom ou quantité :", item);
      if (newName !== null && newName.trim() && newName.trim() !== item)
        await action("/api/shopping/items/rename", {item,new_name:newName.trim()});
    });
    li.append(label,button,rename,deleteButton(item)); return li;
  }));
  el("shopping-completed").replaceChildren(...completed.items.map(item => {
    const li=document.createElement("li"), label=document.createElement("span"); label.textContent=item + " ";
    li.append(label,makeButton("Remettre", item, () => action("/api/shopping/items/restore",{item})),deleteButton(item));
    return li;
  }));
  feedback(result.items.length ? `${result.items.length} article(s).` : "La liste est vide.");
}
el("shopping-config").addEventListener("submit", async event => {
  event.preventDefault();
  try { await api("/api/shopping/config", {entity_id:el("shopping-entity").value.trim()}); feedback("Liste enregistrée. Affichez la liste pour vérifier la connexion."); el("shopping-items").replaceChildren(); }
  catch(error) { feedback(error.message); }
});
el("shopping-add").addEventListener("submit", async event => {
  event.preventDefault();
  const item=el("shopping-item").value.trim();
  try { const result=await api("/api/shopping/items", {item}); el("shopping-item").value=""; try { await refresh(); feedback(result.message); } catch(error) { feedback(result.message + " Lecture de la liste impossible : " + error.message); } }
  catch(error) { feedback(error.message); }
});
el("shopping-refresh").addEventListener("click", () => refresh().catch(error => feedback(error.message)));
el("shopping-purge").addEventListener("click", async () => {
  if (!window.confirm("Supprimer définitivement tous les articles, y compris les articles cochés ?")) return;
  const button=el("shopping-purge"); button.disabled=true;
  try { const result=await api("/api/shopping/items/purge", {confirm_delete:true}); try { await refresh(); feedback(result.message); } catch(error) { feedback(result.message + " Lecture de la liste impossible : " + error.message); } }
  catch(error) { feedback(error.message); } finally { button.disabled=false; }
});
api("/api/shopping/config").then(data => { if(data.entity_id) el("shopping-entity").value=data.entity_id; }).catch(error => feedback(error.message));
