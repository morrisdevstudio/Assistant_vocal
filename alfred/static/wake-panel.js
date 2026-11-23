import {PCMResampler} from "./wake-audio.mjs";
const el=id=>document.getElementById(id);
let snapshot=null,browser=null,generation=0,saving=false;
const tell=(source,text)=>{el(`wake-${source}-feedback`).textContent=text;};
async function api(path,method="GET",value){
  const response=await fetch(path,{method,headers:{"Content-Type":"application/json"},
    ...(value===undefined?{}:{body:JSON.stringify(value)})});
  const data=await response.json();
  if(!response.ok)throw new Error(typeof data.detail==="string"?data.detail:"Réglage impossible.");
  return data;
}
function renderSource(source,fill=false){
  const config=snapshot.settings[source];
  if(fill){
    el(`wake-${source}-engine`).value=config.engine;
    el(`wake-${source}-phrase`).value=config.phrase;
    el(`wake-${source}-variants`).value=config.variants.join(", ");
    el(`wake-${source}-threshold`).value=config.threshold;
    const select=el(`wake-${source}-model`);select.replaceChildren();
    for(const model of snapshot.models){
      const option=document.createElement("option");option.value=model.id;
      option.textContent=`${model.label} · « ${model.phrase} »`;select.append(option);
    }
    select.value=config.model;
  }
  const stt=el(`wake-${source}-engine`).value==="stt";
  el(`wake-${source}-stt`).hidden=!stt;
  el(`wake-${source}-oww`).hidden=stt;
  el(`wake-${source}-save`).disabled=saving||snapshot.busy;
}
async function refresh(fill=false){
  try{
    snapshot=await api("/api/wake/config");
    for(const source of ["browser","esp32"])renderSource(source,fill);
    el("wake-browser-start").disabled=Boolean(browser)||snapshot.busy;
    el("wake-browser-stop").disabled=!browser;
    if(!browser)tell("browser","Veille fermée. Cliquez sur Activer pour ouvrir ce microphone.");
  }catch(error){tell("browser",error.message);}
}
async function stopBrowser(reason="Veille arrêtée. Micro fermé.",notify=true){
  generation++;
  const current=browser;browser=null;
  if(current){
    clearInterval(current.ping);
    current.socket?.close();
    current.stream?.getTracks().forEach(track=>track.stop());
    current.node?.disconnect();current.source?.disconnect();
    await current.context?.close().catch(()=>{});
  }
  if(notify)window.alfredVoice?.stopWakeConversation();
  tell("browser",reason);
  el("wake-browser-start").disabled=false;el("wake-browser-stop").disabled=true;
}
async function startBrowser(){
  await stopBrowser("Préparation du microphone…",false);
  const id=generation;
  const current={socket:null,stream:null,context:null,node:null,source:null,sending:false,ping:null};
  browser=current;
  try{
    if(!window.isSecureContext||!navigator.mediaDevices?.getUserMedia)throw new Error("Le microphone nécessite HTTPS ou localhost.");
    await window.alfredVoice.prepareWake();
    current.stream=await navigator.mediaDevices.getUserMedia({audio:{channelCount:1,echoCancellation:true,noiseSuppression:true,autoGainControl:true},video:false});
    if(id!==generation){current.stream.getTracks().forEach(t=>t.stop());return;}
    current.context=new AudioContext({sampleRate:16000});
    await current.context.audioWorklet.addModule("/static/recorder-worklet.js");
    if(id!==generation)return;
    const resampler=new PCMResampler(current.context.sampleRate);
    current.source=current.context.createMediaStreamSource(current.stream);
    current.node=new AudioWorkletNode(current.context,"alfred-recorder");
    const address=new URL("/api/wake/browser",location.href);address.protocol=location.protocol==="https:"?"wss:":"ws:";
    current.socket=new WebSocket(address);
    current.node.port.onmessage=event=>{
      if(id!==generation||!current.sending||!(event.data instanceof Float32Array))return;
      const pcm=resampler.push(event.data);
      if(current.socket.readyState===WebSocket.OPEN){
        if(current.socket.bufferedAmount>32000){stopBrowser("Connexion trop lente. Veille fermée.");return;}
        if(pcm.byteLength)current.socket.send(pcm);
      }
    };
    current.socket.onmessage=async event=>{
      if(id!==generation)return;
      const value=JSON.parse(event.data);
      if(value.type==="ready"){
        current.sending=true;tell("browser","Veille active sur ce microphone. Aucun appel IA avant le mot d’appel.");
      }else if(value.type==="detected")tell("browser","Mot reconnu. Je vous écoute…");
      else if(value.type==="command"){
        current.sending=false;
        tell("browser","Veille en pause pendant la conversation.");
        await window.alfredVoice.receiveWake(value);
      }else if(value.type==="stopped")await stopBrowser(value.reason);
    };
    current.socket.onerror=()=>{if(id===generation)stopBrowser("Connexion de veille impossible. Micro fermé.");};
    current.socket.onclose=()=>{if(id===generation)stopBrowser("Connexion interrompue. Réactivez la veille.");};
    current.ping=setInterval(()=>{if(current.socket.readyState===WebSocket.OPEN)current.socket.send(JSON.stringify({type:"ping"}));},5000);
    current.stream.getTracks().forEach(track=>track.addEventListener("ended",()=>{if(id===generation)stopBrowser("Microphone déconnecté.");}));
    current.source.connect(current.node);current.node.connect(current.context.destination);
    await current.context.resume();
    el("wake-browser-start").disabled=true;el("wake-browser-stop").disabled=false;
  }catch(error){if(id===generation)await stopBrowser(error.message||"Microphone indisponible.");}
}
for(const source of ["browser","esp32"]){
  el(`wake-${source}-engine`).addEventListener("change",()=>renderSource(source));
  el(`wake-${source}-save`).addEventListener("click",async()=>{
    saving=true;
    try{
      const value={engine:el(`wake-${source}-engine`).value,model:el(`wake-${source}-model`).value||snapshot.settings[source].model,
        threshold:Number(el(`wake-${source}-threshold`).value),phrase:el(`wake-${source}-phrase`).value,
        variants:el(`wake-${source}-variants`).value.split(",").map(v=>v.trim()).filter(Boolean)};
      snapshot=await api(`/api/wake/config/${source}`,"PUT",value);
      renderSource(source,true);tell(source,"Réglages enregistrés.");
    }catch(error){tell(source,error.message);}finally{saving=false;renderSource(source);}
  });
}
el("wake-browser-start").addEventListener("click",startBrowser);
el("wake-browser-stop").addEventListener("click",()=>stopBrowser());
el("wake-model-import").addEventListener("submit",async event=>{
  event.preventDefault();const file=el("wake-model-file").files[0];
  if(!file||file.size>10*1024*1024){el("wake-import-feedback").textContent="Choisissez un fichier ONNX de dix Mo au maximum.";return;}
  const button=el("wake-import-button");button.disabled=true;
  el("wake-import-feedback").textContent="Vérification du modèle…";
  try{
    const bytes=new Uint8Array(await file.arrayBuffer());let binary="";
    for(let at=0;at<bytes.length;at+=8192)binary+=String.fromCharCode(...bytes.subarray(at,at+8192));
    const result=await api("/api/wake/models","POST",{label:el("wake-model-label").value,phrase:el("wake-model-phrase").value,model_base64:btoa(binary)});
    await refresh(true);el("wake-import-feedback").textContent=`Modèle « ${result.label} » ajouté. Sélectionnez-le puis enregistrez.`;
  }catch(error){el("wake-import-feedback").textContent=error.message;}finally{button.disabled=false;}
});
window.addEventListener("alfred-wake-resume",()=>{
  if(browser?.socket.readyState===WebSocket.OPEN)browser.socket.send(JSON.stringify({type:"resume"}));
});
window.addEventListener("alfred-wake-stop",()=>stopBrowser("Veille arrêtée. Micro fermé.",false));
document.addEventListener("visibilitychange",()=>{if(document.hidden)stopBrowser("Page en arrière-plan. Veille fermée.");});
window.addEventListener("pagehide",()=>stopBrowser("Page fermée."));
function wakeViewVisible(){const view=document.querySelector('[data-view="voice"]');return Boolean(view&&!view.hidden);}
await refresh(true);
setInterval(()=>{if(!document.hidden&&wakeViewVisible())refresh();},3000);
window.addEventListener("hashchange",()=>{if(wakeViewVisible())refresh();});
document.addEventListener("visibilitychange",()=>{if(!document.hidden&&wakeViewVisible())refresh();});
