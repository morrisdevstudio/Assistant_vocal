const el=id=>document.getElementById(id);
let config={configured:false};
function message(text,error=false){el("ai-feedback").textContent=text;el("ai-feedback").classList.toggle("error",error);}
function display(value){
  config=value;
  el("ai-state").textContent=value.configuration_error?"Configuration à vérifier":value.access_verified?"Accès vérifié":value.configured?"Clé configurée · accès à tester":"Clé à configurer";
  if(value.model)el("ai-model").value=value.model;
  el("ai-key").required=!value.configured;
  el("ai-key").disabled=!!value.key_from_environment;
  el("ai-save").disabled=!!value.key_from_environment;
  el("ai-check").disabled=!value.configured;
  el("ai-storage").textContent=value.storage?`Stockage : ${value.storage}. La clé n’est jamais renvoyée au navigateur.`:"Configuration locale à vérifier.";
  if(!value.configured)el("ai-settings").open=true;
  window.dispatchEvent(new CustomEvent("alfred-ai-changed",{detail:value}));
}
async function api(path,body){
  const response=await fetch(path,body===undefined?{}:{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});
  const result=await response.json();
  if(!response.ok)throw new Error(typeof result.detail==="string"?result.detail:"La demande n’a pas pu être traitée.");
  return result;
}
el("ai-config-form").addEventListener("submit",async event=>{
  event.preventDefault();
  const key=el("ai-key").value.trim();const body={model:el("ai-model").value.trim()};if(key)body.api_key=key;
  el("ai-key").value="";el("ai-save").disabled=true;
  try{const result=await api("/api/ai/config",body);display(result);message("Configuration enregistrée. Testez l’accès pour vérifier la clé et le modèle.");}
  catch(error){message(error.message,true);}
  finally{el("ai-key").value="";el("ai-save").disabled=!!config.key_from_environment;}
});
el("ai-check").addEventListener("click",async()=>{
  el("ai-check").disabled=true;message("Vérification de l’accès par une courte requête…");
  try{const result=await api("/api/ai/check",{});display(await api("/api/ai/config"));message(`Accès validé · ${result.model} · ${result.llm_ms} ms. Vous pouvez passer en mode Conversation.`);}
  catch(error){message(error.message,true);}
  finally{el("ai-check").disabled=!config.configured;}
});
try{display(await api("/api/ai/config"));}catch{message("Configuration indisponible. Rechargez la page après le démarrage du service.",true);}
