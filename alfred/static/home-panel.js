const el=id=>document.getElementById(id);
let home={configured:false};
const makeHomeSession=()=>"home-"+Date.now().toString(36)+"-"+Math.random().toString(36).slice(2,12);
let homeSessionId=(()=>{try{const saved=sessionStorage.getItem("alfred-home-session");if(saved)return saved;const value=globalThis.crypto?.randomUUID?.()||makeHomeSession();sessionStorage.setItem("alfred-home-session",value);return value;}catch{return makeHomeSession();}})();
function message(text,error=false){el("home-feedback").textContent=text;el("home-feedback").classList.toggle("error",error);}
function showConfirmation(text){el("home-confirmation-text").textContent=text;el("home-confirmation").hidden=false;}
function hideConfirmation(){el("home-confirmation").hidden=true;}
function display(value){
  home=value;
  el("home-state").textContent=value.configuration_error?"Configuration à vérifier":value.verified?"Connexion vérifiée":value.configured?"Jeton configuré · connexion à tester":"À configurer";
  if(value.base_url)el("home-url").value=value.base_url;
  if(value.room)el("home-room").value=value.room;
  el("home-token").required=!value.configured;
  el("home-token").disabled=!!value.from_environment;
  el("home-save").disabled=!!value.from_environment;
  el("home-check").disabled=!value.configured;
  el("home-off-all").disabled=!value.configured;
  el("home-off-room").disabled=!value.configured;
  el("home-send").disabled=!value.configured;
  el("home-storage").textContent=value.storage?("Stockage : "+value.storage+". Le jeton n’est jamais renvoyé au navigateur."):"Configuration locale à vérifier.";
  if(!value.configured)el("home-settings").open=true;
  window.dispatchEvent(new CustomEvent("alfred-home-changed",{detail:value}));
}
async function api(path,body){
  const response=await fetch(path,body===undefined?{}:{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});
  const type=response.headers.get("content-type")||"";
  let result=null;
  if(type.indexOf("application/json")>=0)result=await response.json().catch(()=>null);
  if(!response.ok){
    if(response.status===404)throw new Error("Route absente : un ancien Alfred tourne encore. Arrêtez-le puis relancez le service.");
    throw new Error(result&&typeof result.detail==="string"?result.detail:"La demande n’a pas pu être traitée.");
  }
  if(result===null)throw new Error("Réponse inattendue du service Alfred.");
  return result;
}
async function run(path,body,success){
  hideConfirmation();
  message("Exécution en cours…");
  for(const id of ["home-check","home-off-all","home-off-room","home-send","home-save","home-confirmation-yes","home-confirmation-no"])el(id).disabled=true;
  try{
    const result=await api(path,path==="/api/home/command"?{session_id:homeSessionId,...body}:body);
    display(await api("/api/home/config"));
    if(result&&result.status==="confirmation"){showConfirmation(result.reply);message(result.reply);}
    else message(success(result));
  }catch(error){message(error.message,true);display(await api("/api/home/config").catch(()=>home));}
  finally{for(const id of ["home-confirmation-yes","home-confirmation-no"])el(id).disabled=false;}
}
async function answerConfirmation(accept){
  await run("/api/home/command",{text:accept?"oui":"non"},result=>result.reply||"Commande exécutée.");
}
el("home-config-form").addEventListener("submit",async event=>{
  event.preventDefault();
  const token=el("home-token").value.trim();
  const body={base_url:el("home-url").value.trim(),room:el("home-room").value.trim()};
  if(token)body.token=token;
  el("home-token").value="";
  message("Enregistrement local…");
  try{const result=await api("/api/home/config",body);display(result);message("Configuration enregistrée. Testez la connexion pour vérifier le jeton.");}
  catch(error){message(error.message,true);}
  finally{el("home-token").value="";}
});
el("home-check").addEventListener("click",()=>run("/api/home/check",{},
  result=>"Connexion OK · "+(result.location_name||"Home Assistant")+" · "+result.version+" · "+result.lights+" lumière"+(result.lights===1?"":"s")+", "+result.lights_on+" allumée"+(result.lights_on===1?"":"s")+"."));
el("home-off-all").addEventListener("click",()=>run("/api/home/command",{text:"Éteins toutes les lumières"},
  result=>result.reply||"Commande exécutée."));
el("home-off-room").addEventListener("click",()=>run("/api/home/command",{text:"Éteins la lumière"},
  result=>result.reply||"Commande exécutée."));
el("home-command-form").addEventListener("submit",async event=>{
  event.preventDefault();
  const text=el("home-text").value.trim();
  if(!text)return;
  await run("/api/home/command",{text},result=>result.reply||"Commande exécutée.");
  el("home-text").value="";
});
el("home-confirmation-yes").addEventListener("click",()=>answerConfirmation(true));
el("home-confirmation-no").addEventListener("click",()=>answerConfirmation(false));
try{display(await api("/api/home/config"));}catch{message("Configuration Home Assistant indisponible. Rechargez la page.",true);}

let catalog=[], rooms=[], editing=null, saving=false;
let catalogSort={key:"area",direction:1};
const catalogCollator=new Intl.Collator("fr",{sensitivity:"base",numeric:true});
const catalogFeedback=el("home-catalog-feedback");
const editor=el("home-device-editor");
const roomField=el("home-device-room");
const roomIcon=el("home-device-room-icon");
const saveButton=el("home-device-submit");
const editorError=el("home-device-editor-error");

function addOption(select,value,label=value){
  const option=document.createElement("option");
  option.value=value;
  option.textContent=label;
  select.append(option);
}
function deviceSettings(item){
  const room=item.alfred_area===item.ha_area?"":item.alfred_area||"";
  return {alfred_name:item.alfred_name||"",alfred_area:room,aliases:item.aliases||[],
    allowed:item.allowed,confirmation_required:item.confirmation_required,
    ...(item.domain==="light"?{light_type:item.light_type||"main"}:{})};
}
function editorChanges(){
  const draft={alfred_name:el("home-device-name").value.trim(),alfred_area:roomField.value,
    aliases:[...new Set(el("home-device-aliases").value.split(",").map(alias=>alias.trim()).filter(Boolean))],
    allowed:el("home-device-allowed").checked,confirmation_required:el("home-device-confirmation").checked,
    ...(editing.domain==="light"?{light_type:el("home-device-light-type").value}:{})};
  const initial=deviceSettings(editing);
  return Object.fromEntries(Object.entries(draft).filter(([key,value])=>JSON.stringify(value)!==JSON.stringify(initial[key])));
}
function openEditor(item){
  editing=item;
  const initial=deviceSettings(item);
  el("home-device-editor-title").textContent="Modifier "+item.name;
  el("home-device-name").value=initial.alfred_name;
  el("home-device-name").placeholder=item.ha_name;
  el("home-device-original-name").textContent="Home Assistant · "+item.ha_name;
  roomField.replaceChildren();
  addOption(roomField,"",item.ha_area??"Sans pièce");
  if(initial.alfred_area&&!rooms.includes(initial.alfred_area)){
    addOption(roomField,initial.alfred_area,initial.alfred_area+" · ancienne affectation");
  }
  for(const room of rooms)if(room!==item.ha_area)addOption(roomField,room);
  roomField.value=initial.alfred_area;
  el("home-device-original-room").textContent=item.ha_area?"Pièce Home Assistant · "+item.ha_area:"";
  roomIcon.hidden=Boolean(initial.alfred_area)||!item.ha_area;
  el("home-device-light-type-field").hidden=item.domain!=="light";
  el("home-device-light-type").value=initial.light_type||"main";
  el("home-device-allowed").checked=initial.allowed;
  el("home-device-confirmation").checked=initial.confirmation_required;
  el("home-device-aliases").value=initial.aliases.join(", ");
  el("home-device-original-aliases").textContent="Alias Home Assistant · "+(item.ha_aliases?.join(", ")||"Aucun");
  editorError.hidden=true;
  saveButton.disabled=true;
  editor.showModal();
  el("home-device-name").focus();
}
editor.addEventListener("cancel",event=>{if(saving)event.preventDefault();});
editor.addEventListener("close",()=>{
  if(!editing)return;
  const button=el("home-catalog-list").querySelector(`[data-edit-id="${editing.entity_id}"]`);
  editing=null;
  (button||el("home-catalog-search")).focus();
});
el("home-device-cancel").addEventListener("click",()=>{if(!saving)editor.close();});
const form=el("home-device-editor-form");
form.addEventListener("input",()=>{
  if(editing){
    saveButton.disabled=saving||!Object.keys(editorChanges()).length;
    roomIcon.hidden=Boolean(roomField.value)||!editing.ha_area;
  }
});
form.addEventListener("submit",async event=>{
  event.preventDefault();
  if(saving||!editing)return;
  const changes=editorChanges();
  if(!Object.keys(changes).length)return;
  const item=editing;
  saving=true;
  el("home-device-editor-fields").disabled=el("home-device-cancel").disabled=saveButton.disabled=true;
  saveButton.textContent="Enregistrement…";
  editorError.hidden=true;
  try{
    const response=await fetch("/api/home/devices",{method:"PATCH",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({id:item.entity_id,settings:changes})});
    const data=await response.json().catch(()=>null);
    if(!response.ok||!data?.settings){
      throw new Error(typeof data?.detail==="string"?data.detail:"Enregistrement impossible.");
    }
    Object.assign(item,data.settings);
    item.name=item.alfred_name||item.ha_name;
    item.area=item.alfred_area||item.ha_area;
    updateCatalogFilters();
    renderCatalog();
    catalogFeedback.textContent="Réglages enregistrés.";
    editor.close();
    if(changes.light_type&&item.members)void refreshCatalog();
  }catch(error){
    editorError.textContent=error.message;
    editorError.hidden=false;
  }finally{
    saving=false;
    el("home-device-editor-fields").disabled=el("home-device-cancel").disabled=false;
    saveButton.disabled=!editor.open;
    saveButton.textContent="Valider";
  }
});
function renderCatalog(){
  const list=el("home-catalog-list"), search=el("home-catalog-search").value.toLocaleLowerCase(), area=el("home-catalog-area").value, domain=el("home-catalog-domain").value;
  list.replaceChildren();
  const visible=catalog.filter(x=>(!area||(x.area||"Sans pièce")===area)&&(!domain||x.domain===domain)&&[x.name,x.ha_name,x.entity_id,x.device,x.area,...(x.aliases||[]),...(x.ha_aliases||[])].some(v=>(v||"").toLocaleLowerCase().includes(search)));
  if(!visible.length){list.textContent="Aucune entité correspondante.";return;}
  const sortValue=(item,key)=>key==="area"?(item.area||"Sans pièce"):(item[key]||"");
  visible.sort((a,b)=>catalogSort.direction*catalogCollator.compare(sortValue(a,catalogSort.key),sortValue(b,catalogSort.key))||catalogCollator.compare(a.name||"",b.name||"")||catalogCollator.compare(a.entity_id,b.entity_id));
  const table=document.createElement("table"), head=document.createElement("thead"), header=document.createElement("tr"), body=document.createElement("tbody");
  for(const [title,key] of [["Nom","name"],["Pièce","area"],["Type","domain"],["Accès",null],["Confirmation",null],["Alias",null],["Modifier",null]]){
    const th=document.createElement("th");th.scope="col";
    if(key){
      const active=catalogSort.key===key, button=document.createElement("button");
      th.setAttribute("aria-sort",active?(catalogSort.direction===1?"ascending":"descending"):"none");
      button.type="button";button.className="catalog-sort";button.dataset.sortKey=key;
      button.textContent=title+(active?(catalogSort.direction===1?" ↑":" ↓"):" ↕");
      button.addEventListener("click",()=>{
        catalogSort={key,direction:catalogSort.key===key?-catalogSort.direction:1};
        renderCatalog();
        list.querySelector(`[data-sort-key="${key}"]`)?.focus();
      });
      th.append(button);
    }else th.textContent=title;
    header.append(th);
  }
  head.append(header);table.append(head,body);list.append(table);
  for(const item of visible){
    const row=document.createElement("tr"), name=document.createElement("th");
    name.scope="row";
    name.textContent=item.name;
    name.title=item.entity_id;
    row.append(name);
    for(const [label,value] of [["Pièce",item.area||"Sans pièce"],["Type",item.domain],
      ["Accès",item.allowed?"Autorisé":"Exclu"],["Confirmation",item.confirmation_required?"Activée":"Désactivée"],
      ["Alias",item.aliases?.join(", ")||"Aucun"]]){
      const cell=document.createElement("td");
      cell.textContent=value;
      cell.setAttribute("data-label",label);
      row.append(cell);
    }
    const cell=document.createElement("td"), button=document.createElement("button");
    cell.className="catalog-edit-cell";
    button.type="button";
    button.dataset.editId=item.entity_id;
    button.className="catalog-edit";
    button.textContent="✎";
    button.title="Modifier "+item.name;
    button.setAttribute("aria-label",button.title);
    button.setAttribute("aria-haspopup","dialog");
    button.addEventListener("click",()=>openEditor(item));
    cell.append(button);row.append(cell);body.append(row);
  }
}
function updateCatalogFilters(){
  for(const [id,values] of [["home-catalog-area",catalog.map(x=>x.area||"Sans pièce")],["home-catalog-domain",catalog.map(x=>x.domain)]]){
    const select=el(id), selected=select.value;
    while(select.options.length>1)select.remove(1);
    if(selected&&!values.includes(selected))values.push(selected);
    for(const value of [...new Set(values)].sort(catalogCollator.compare))addOption(select,value);
    select.value=selected;
  }
}
async function refreshCatalog(){
  catalogFeedback.textContent="Chargement…";
  try{
    const data=await api("/api/home/catalog");
    catalog=data.entities;
    rooms=[...(data.ha_rooms||[])].sort(catalogCollator.compare);
    updateCatalogFilters();
    renderCatalog();
    catalogFeedback.textContent=`${catalog.length} entité(s) exposée(s) à Assist.`;
  }catch(error){catalog=[];renderCatalog();catalogFeedback.textContent=error.message;}
}
el("home-catalog-refresh").addEventListener("click",refreshCatalog);
for(const id of ["home-catalog-search","home-catalog-area","home-catalog-domain"])el(id).addEventListener("input",renderCatalog);
if(home.configured)refreshCatalog();
