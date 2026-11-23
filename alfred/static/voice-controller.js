import {encodeWav,decodeAudioBase64} from "./audio-utils.mjs";
import {readConversation} from "./conversation-stream.mjs";
import {FollowupPolicy,SpeechTurn} from "./speech-turn.mjs";

const el=id=>document.getElementById(id);
const SAMPLE="Bonsoir. Je suis Alfred. Que puis-je faire pour vous ?";
const followup=new FollowupPolicy();
let state="idle",generation=0,recording=null,controller=null;
let ready={stt_available:false,tts_available:false,tts_voice_id:"phonon-dumby-cpu"};
let sessionId=crypto.randomUUID(),replyUrl=null,previewUrl=null;
let musicDucked=false,musicDuckPending=null;
let wakeConversation=false;
function wakeSignal(name){
  if(typeof window.dispatchEvent==="function")window.dispatchEvent(new CustomEvent(name));
}

function feedback(text,error=false){
  if(el("voice-feedback").textContent!==text)el("voice-feedback").textContent=text;
  el("voice-feedback").classList.toggle("error",error);
}
async function musicVolume(path,keepalive=false){
  const response=await fetch(path,{method:"POST",headers:{"Content-Type":"application/json"},
    body:JSON.stringify({session_id:sessionId}),keepalive});
  return response.ok?response.json():null;
}
async function duckMusicForInteraction(){
  if(musicDucked)return;
  if(!musicDuckPending)musicDuckPending=musicVolume("/api/music/duck")
    .then(result=>{if(result?.owned)musicDucked=true;return result;})
    .catch(()=>null).finally(()=>{musicDuckPending=null;});
  await musicDuckPending;
}
async function restoreMusicAfterInteraction(){
  if(musicDuckPending)await musicDuckPending;
  if(!musicDucked)return;
  musicDucked=false;
  try{await musicVolume("/api/music/restore");}catch{}
}
function buttons(){
  el("voice-record").textContent=state==="listening"?"Fermer l’écoute":state==="recording"?"Terminer et envoyer":"Parler au micro";
  el("voice-record").disabled=!ready.stt_available || !ready.tts_available || !["idle","listening","recording"].includes(state);
  el("voice-sample").disabled=!ready.tts_available || state!=="idle";
  el("voice-cancel").disabled=state==="idle" && !replyUrl && !followup.armed;
  el("voice-cancel").textContent=followup.armed?"Arrêter la conversation":"Annuler / arrêter la lecture";
  el("chat-send").disabled=!ready.tts_available || state!=="idle" || el("voice-mode").value!=="conversation";
  el("voice-mode").disabled=state!=="idle";
  el("voice-choice").disabled=state!=="idle" || (!ready.tts_available && !(ready.voices||[]).some(voice=>voice.available));
}
function showVoiceStatus(){
  for(const voice of ready.voices||[]){
    const option=el("voice-choice").querySelector(`option[value="${voice.id}"]`);
    if(option)option.disabled=!voice.available;
  }
  if(ready.tts_voice_id)el("voice-choice").value=ready.tts_voice_id;
  const names={"phonon-dumby-cpu":"Dumby","phonon-alfred-cpu":"Alfred cloné","phonon-arnaud-cpu":"Arnaud","phonon-lucien-cpu":"Lucien"};
  const label=names[ready.tts_voice_id]||"Phonon local";
  const stt=(ready.stt_model||"Transcription locale").split(" · ")[0];
  el("voice-models").textContent=ready.stt_available && ready.tts_available?`${stt} + Phonon · ${label} · CPU`:"Moteurs à préparer";
}
function updateAI(){
  el("voice-mode").querySelector('option[value="conversation"]').disabled=false;
  buttons();
}
window.addEventListener("alfred-ai-changed",event=>updateAI(event.detail));
el("voice-mode").addEventListener("change",()=>{followup.stop();buttons();});
el("voice-auto").addEventListener("change",()=>{
  if(!el("voice-auto").checked){
    followup.stop();
    if(recording?.automatic && !recording.gate?.hasSpeech)cancel("Écoute automatique désactivée. Micro fermé.");
  }
  buttons();
});
el("voice-choice").addEventListener("change",async()=>{
  const desired=el("voice-choice").value;
  const label={"phonon-dumby-cpu":"Dumby","phonon-alfred-cpu":"Alfred cloné","phonon-arnaud-cpu":"Arnaud","phonon-lucien-cpu":"Lucien"}[desired]||"Phonon";
  state="processing";buttons();feedback(`Changement pour la voix ${label}…`);
  try{
    const response=await request("/api/voice/config",{voice:desired});if(!response.ok)throw new Error();
    ready={...ready,...await response.json()};showVoiceStatus();
    feedback(`Voix ${label} active. Écoutez-la pour confirmer le timbre.`);
  }catch(error){
    el("voice-choice").value=ready.tts_voice_id||"phonon-dumby-cpu";feedback(error.message||"Le changement de voix a échoué.",true);
  }finally{state="idle";buttons();}
});

function clearAudio(id,url){
  const audio=el(id);audio.pause();audio.removeAttribute("src");audio.load();
  if(url)URL.revokeObjectURL(url);
}
async function closeRecording(session){
  if(!session)return;
  clearTimeout(session.timeout);clearInterval(session.counter);
  session.stream?.getTracks().forEach(track=>track.stop());
  session.node?.disconnect();session.source?.disconnect();
  if(session.context && session.context.state!=="closed")await session.context.close().catch(()=>{});
  session.chunks=[];
  if(session.gate){session.gate.chunks=[];session.gate.preRoll=[];}
}
async function cancel(message="Conversation arrêtée. Micro fermé.",keepWake=false){
  generation++;followup.stop();controller?.abort();controller=null;
  const previous=recording;recording=null;
  state="idle";buttons();feedback(message);
  clearAudio("voice-reply",replyUrl);replyUrl=null;el("voice-reply").hidden=true;
  clearAudio("voice-preview",previewUrl);previewUrl=null;el("voice-preview-details").hidden=true;
  await closeRecording(previous);
  await restoreMusicAfterInteraction();
  if(keepWake && wakeConversation)wakeSignal("alfred-wake-resume");
  else if(!keepWake){wakeConversation=false;wakeSignal("alfred-wake-stop");}
}
async function request(path,body,type="application/json",extraHeaders={}){
  controller=new AbortController();
  const response=await fetch(path,{method:"POST",headers:{"Content-Type":type,...extraHeaders},
    body:type==="application/json"?JSON.stringify(body):body,signal:controller.signal});
  if(!response.ok){const result=await response.json();throw new Error(typeof result.detail==="string"?result.detail:"La demande audio n’a pas pu être traitée.");}
  return response;
}
async function conversationResponse(response,id){
  let answer="",completed=null;
  window.renderInternetSources?.([]);
  el("voice-answer").textContent="";el("voice-timings").textContent="";
  await readConversation(response,event=>{
    if(id!==generation)return;
    if(event.type==="phase")feedback({transcribing:"Micro fermé. Transcription locale…",thinking:"Alfred prépare sa réponse avec Command Code…",speaking:"Préparation de la voix locale…",home:"Commande de la maison exécutée localement…",music:"Commande musicale exécutée localement…",timer:"Traitement local des minuteurs…"}[event.phase]||"Traitement…");
    if(event.type==="transcript")el("voice-transcript").textContent=event.text||"Aucune parole reconnue.";
    if(event.type==="identity" && el("voice-identity"))el("voice-identity").textContent=event.state==="recognized"?"Voix reconnue (essai) : "+event.name:event.state==="unknown"?"Voix non reconnue : invité.":"Reconnaissance vocale non calibrée.";
    if(event.type==="delta"){answer+=event.text;el("voice-answer").textContent=answer;}
    if(event.type==="answer"){el("voice-answer").textContent=event.text;window.renderInternetSources?.(event.sources||[]);}
    if(event.type==="done"){completed=event;window.renderInternetSources?.(event.sources||[]);}
  });
  if(id!==generation)return;
  if(completed?.mode==="wake_empty"){
    state="idle";followup.arm();buttons();
    await startRecording({automatic:true,expectedGeneration:generation,deadline:performance.now()+6000,wakeOnly:true});
    return;
  }
  el("voice-timings").textContent = ["home","music","timer"].includes(completed.mode)
    ? "Commande locale · transcription : "+completed.timings.stt_ms+" ms · voix : "+completed.timings.tts_ms+" ms · aucun appel IA"
    : "Transcription : "+completed.timings.stt_ms+" ms · IA : "+completed.timings.llm_ms+" ms · voix : "+completed.timings.tts_ms+" ms";
  const needsReply=completed.needs_reply===true;
  if(!needsReply)followup.stop();
  await duckMusicForInteraction();
  if(completed.audio_url){
    await playURL(completed.audio_url,id,needsReply);
  }else{
    await play(decodeAudioBase64(completed.audio_base64),id,needsReply);
  }
}
async function playURL(url,id,conversationReply=false){
  if(id!==generation)return;
  const previous=replyUrl;replyUrl=null;clearAudio("voice-reply",previous);
  const audio=el("voice-reply");audio.src=url;audio.hidden=false;
  state="playing";
  if(conversationReply)followup.expectReply(id);
  buttons();
  try{
    await audio.play();
    if(id===generation)feedback(followup.armed?"Alfred répond. L’écoute de 8 secondes commencera à la fin.":"Lecture en cours. Vous pouvez l’arrêter à tout moment.");
  }catch{
    if(id===generation){state="idle";buttons();await restoreMusicAfterInteraction();feedback("Audio prêt. Appuyez sur Lecture ci-dessous ; le micro reste fermé pendant la lecture.");}
  }
}
async function play(blob,id,conversationReply=false){
  if(id!==generation)return;
  const previous=replyUrl;replyUrl=null;clearAudio("voice-reply",previous);
  replyUrl=URL.createObjectURL(blob);
  const audio=el("voice-reply");audio.src=replyUrl;audio.hidden=false;
  state="playing";
  if(conversationReply)followup.expectReply(id);
  buttons();
  try{
    await audio.play();
    if(id===generation)feedback(followup.armed?"Alfred répond. L’écoute de 8 secondes commencera à la fin.":"Lecture en cours. Vous pouvez l’arrêter à tout moment.");
  }catch{
    if(id===generation){state="idle";buttons();await restoreMusicAfterInteraction();feedback("Audio prêt. Appuyez sur Lecture ci-dessous ; le micro reste fermé pendant la lecture.");}
  }
}
el("voice-reply").addEventListener("ended",async()=>{
  if(!el("voice-reply").getAttribute("src") || !el("voice-reply").ended || recording || !["playing","idle"].includes(state))return;
  const next=followup.ended(generation,performance.now(),{
    enabled:el("voice-auto").checked,conversation:el("voice-mode").value==="conversation",visible:!document.hidden,
  });
  state="idle";buttons();
  if(next)startRecording({automatic:true,expectedGeneration:next.generation,deadline:next.deadline});
  else{followup.stop();await restoreMusicAfterInteraction();buttons();feedback("Réponse terminée. Micro fermé.");if(wakeConversation)wakeSignal("alfred-wake-resume");}
});
el("voice-reply").addEventListener("pause",()=>{
  if(state==="playing" && el("voice-reply").paused){state="idle";buttons();}
});
el("voice-reply").addEventListener("error",async()=>{
  if(!el("voice-reply").getAttribute("src"))return;
  followup.stop();state="idle";buttons();await restoreMusicAfterInteraction();feedback("Lecture audio impossible. Le micro reste fermé.",true);
});
// Une réécoute manuelle ne doit pas être enregistrée comme une nouvelle demande.
for(const identifier of ["voice-reply","voice-preview"]){
  el(identifier).addEventListener("play",()=>{
    if(!recording)return;
    generation++;followup.stop();const previous=recording;recording=null;
    state="playing";closeRecording(previous);buttons();feedback("Écoute fermée pendant la réécoute audio.");
  });
}

function gateResult(session,result,id){
  if(id!==generation || recording!==session || !["listening","recording"].includes(state))return;
  if(result.started){state="recording";buttons();feedback("Je vous écoute. La phrase sera envoyée après une seconde de silence.");}
  if(result.done){finishRecording();return;}
  if(!result.hasSpeech){
    const seconds=Math.ceil(result.remainingMs/1000);
    feedback(session.automatic?`À vous · encore ${seconds} s pour parler. Micro ouvert.`:"Micro ouvert. Parlez : la phrase sera envoyée automatiquement après une pause.");
  }
}
async function startRecording({automatic=false,expectedGeneration=null,deadline=null,wakeOnly=false}={}){
  if(automatic && (expectedGeneration!==generation || !followup.armed || (!el("voice-auto").checked&&!wakeOnly) || document.hidden))return;
  if(!window.isSecureContext || !navigator.mediaDevices?.getUserMedia){
    followup.stop();feedback("Le micro demande localhost ou une connexion HTTPS et un navigateur compatible.",true);buttons();return;
  }
  if(automatic && performance.now()>=deadline){await cancel("Fenêtre de conversation terminée. Micro fermé.",true);return;}
  if(!automatic)await cancel();
  const id=++generation;
  const isConversation=el("voice-mode").value==="conversation";
  if(isConversation)await duckMusicForInteraction();
  if(!automatic && isConversation && el("voice-auto").checked)followup.arm();
  const session={chunks:[],frames:0,stream:null,context:null,node:null,source:null,gate:null,automatic,isConversation};
  recording=session;state="asking";buttons();
  feedback(automatic?"Réouverture du micro pour votre réponse…":"Autorisez le micro du navigateur pour parler à Alfred.");
  if(automatic)session.timeout=setTimeout(()=>{
    if(id===generation && state==="asking")cancel("Fenêtre de conversation terminée. Micro fermé.",true);
  },Math.max(0,deadline-performance.now()));
  try{
    // Aucune capture pendant le calcul ou la lecture de la réponse précédente.
    el("voice-preview").pause();el("voice-reply").pause();
    session.stream=await navigator.mediaDevices.getUserMedia({audio:{channelCount:1,echoCancellation:true,noiseSuppression:true,autoGainControl:true},video:false});
    if(id!==generation){await closeRecording(session);return;}
    session.context=new AudioContext({sampleRate:48000});
    await session.context.audioWorklet.addModule("/static/recorder-worklet.js");
    if(id!==generation){await closeRecording(session);return;}
    session.source=session.context.createMediaStreamSource(session.stream);
    session.node=new AudioWorkletNode(session.context,"alfred-recorder");
    if(isConversation)session.gate=new SpeechTurn({sampleRate:session.context.sampleRate,deadline:automatic?deadline:performance.now()+30000});
    session.node.port.onmessage=event=>{
      if(event.data==="flushed"){session.flushed?.();return;}
      if(id!==generation || recording!==session)return;
      if(session.gate){
        if(session.gate.done)return;
        const result=session.gate.push(event.data,performance.now());gateResult(session,result,id);
      }else{
        const remaining=session.context.sampleRate*30-session.frames;
        const chunk=event.data.slice(0,Math.max(0,remaining));
        if(chunk.length){session.chunks.push(chunk);session.frames+=chunk.length;}
        if(remaining<=event.data.length && state==="recording")finishRecording();
      }
    };
    state=isConversation?"listening":"recording";buttons();
    session.source.connect(session.node);session.node.connect(session.context.destination);
    await session.context.resume();
    if(id!==generation || recording!==session){await closeRecording(session);return;}
    clearTimeout(session.timeout);
    if(session.gate){
      gateResult(session,session.gate.poll(performance.now()),id);
      if(recording!==session || state==="processing")return;
      session.counter=setInterval(()=>gateResult(session,session.gate.poll(performance.now()),id),100);
      const checkDeadline=()=>{
        if(id!==generation || recording!==session || session.gate.hasSpeech)return;
        const result=session.gate.poll(performance.now());gateResult(session,result,id);
        // Une amorce de parole juste avant l'échéance dispose seulement du délai
        // nécessaire à sa confirmation, sans prolonger une attente silencieuse.
        if(!result.done && !result.hasSpeech)session.timeout=setTimeout(checkDeadline,
          Math.max(1,session.gate.deadline+session.gate.graceMs+1-performance.now()));
      };
      session.timeout=setTimeout(checkDeadline,Math.max(0,session.gate.deadline-performance.now()));
    }else{
      const started=performance.now();
      feedback("Micro ouvert · parlez, puis cliquez sur « Terminer et envoyer ».");
      session.counter=setInterval(()=>feedback(`Micro ouvert · ${Math.min(30,Math.floor((performance.now()-started)/1000))} / 30 s`),1000);
      session.timeout=setTimeout(finishRecording,30000);
    }
    session.stream.getAudioTracks().forEach(track=>track.addEventListener("ended",()=>{
      if(id===generation && ["listening","recording","asking"].includes(state))cancel("Micro déconnecté. Conversation arrêtée.");
    }));
  }catch(error){
    await closeRecording(session);if(id!==generation)return;
    recording=null;followup.stop();state="idle";buttons();await restoreMusicAfterInteraction();
    const messages={NotAllowedError:"Accès au micro refusé. Vous pouvez l’autoriser dans les permissions du navigateur.",NotFoundError:"Aucun microphone trouvé sur ce PC.",NotReadableError:"Le microphone est indisponible ou utilisé par une autre application."};
    feedback(messages[error.name]||"Impossible de démarrer le micro. Conversation arrêtée.",true);
  }
}
async function finishRecording(){
  if(!["recording","listening"].includes(state) || !recording)return;
  const id=generation,session=recording;
  state="processing";buttons();clearTimeout(session.timeout);clearInterval(session.counter);
  if(session.gate && !session.gate.hasSpeech){
    await cancel(session.automatic?"Aucune parole détectée pendant les 8 secondes. Conversation terminée, retour à la veille si elle est active.":"Aucune parole détectée. Micro fermé.",session.automatic);return;
  }
  feedback("Phrase terminée. Fermeture du micro et transcription locale…");
  try{
    if(!session.gate){
      await new Promise(resolve=>{
        let timeout;session.flushed=()=>{clearTimeout(timeout);resolve();};
        timeout=setTimeout(resolve,1000);session.node.port.postMessage("flush");
      });
    }else session.gate.finish();
    if(id!==generation)return;
    const wav=encodeWav(session.gate?session.gate.audioChunks():session.chunks,session.context.sampleRate);
    recording=null;await closeRecording(session);
    if(id!==generation)return;
    clearAudio("voice-preview",previewUrl);previewUrl=URL.createObjectURL(new Blob([wav],{type:"audio/wav"}));
    el("voice-preview").src=previewUrl;el("voice-preview-details").hidden=false;
    if(session.isConversation){
      const headers={"X-Alfred-Session":sessionId};
      if(el("floor").value)headers["X-Alfred-Floor"]=el("floor").value;
      const response=await request("/api/conversation/voice",wav,"audio/wav",headers);
      await conversationResponse(response,id);return;
    }
    const response=await request("/api/voice/turn",wav,"audio/wav");const result=await response.json();
    if(id!==generation)return;
    el("voice-transcript").textContent=result.text||"Aucune parole reconnue.";
    window.renderInternetSources?.([]);
    el("voice-answer").textContent=result.reply_text;
    el("voice-timings").textContent=`Prise : ${result.input_seconds} s · transcription : ${result.timings.stt_ms} ms · voix : ${result.timings.tts_ms} ms`;
    if(result.audio_base64)await play(decodeAudioBase64(result.audio_base64),id);
    else{state="idle";buttons();feedback(result.reply_text);}
  }catch(error){
    await closeRecording(session);if(id!==generation)return;
    recording=null;followup.stop();state="idle";buttons();await restoreMusicAfterInteraction();feedback(error.message,true);
  }
}
el("voice-record").addEventListener("click",()=>["recording","listening"].includes(state)?finishRecording():startRecording());
el("voice-cancel").addEventListener("click",()=>cancel());
el("chat-form").addEventListener("submit",async event=>{
  event.preventDefault();const text=el("chat-text").value.trim();if(!text)return;
  await cancel();const id=++generation;state="processing";buttons();
  el("voice-transcript").textContent=text;feedback("Traitement de votre demande…");
  try{
    await duckMusicForInteraction();
    const response=await request("/api/conversation/text",{text,session_id:sessionId,floor_id:el("floor").value||null});
    await conversationResponse(response,id);
  }catch(error){if(id===generation){followup.stop();state="idle";buttons();feedback(error.message,true);}}
});
el("chat-reset").addEventListener("click",async()=>{
  window.renderInternetSources?.([]);
  await cancel();const previous=sessionId;sessionId=crypto.randomUUID();
  el("voice-answer").textContent="Nouvelle conversation ouverte dans cet onglet.";
  el("voice-transcript").textContent="Votre transcription apparaîtra ici.";
  try{
    const response=await fetch("/api/conversation/reset",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({session_id:previous})});
    if(!response.ok)throw new Error();
    el("voice-answer").textContent="Nouvelle conversation. L’ancien contexte temporaire a été effacé.";
  }catch{feedback("Nouvelle session ouverte ; le serveur n’a pas confirmé l’effacement de l’ancienne.",true);}
});
el("voice-sample").addEventListener("click",async()=>{
  window.renderInternetSources?.([]);
  await cancel();const id=++generation;state="processing";buttons();feedback("Préparation de la voix française locale…");
  try{
    const response=await request("/api/voice/speak",{text:SAMPLE});const blob=await response.blob();if(id!==generation)return;
    el("voice-answer").textContent=SAMPLE;el("voice-timings").textContent=`Synthèse : ${response.headers.get("X-TTS-Ms")} ms`;
    await play(blob,id);
  }catch(error){if(id===generation){state="idle";buttons();feedback(error.message,true);}}
});
document.addEventListener("visibilitychange",()=>{
  if(!document.hidden)return;
  followup.stop();
  if(recording)cancel("Onglet quitté. Micro fermé.");
  buttons();
});
window.addEventListener("pagehide",()=>{
  generation++;followup.stop();controller?.abort();const session=recording;recording=null;
  closeRecording(session);if(replyUrl)URL.revokeObjectURL(replyUrl);if(previewUrl)URL.revokeObjectURL(previewUrl);
  if(musicDucked){musicVolume("/api/music/restore",true).catch(()=>{});musicDucked=false;}
});
try{
  const response=await fetch("/api/voice/status");if(!response.ok)throw new Error();ready=await response.json();
  showVoiceStatus();
  if(!ready.stt_available || !ready.tts_available)feedback("Les modèles vocaux ne sont pas disponibles sur ce service.",true);
  const ai=await fetch("/api/ai/config");if(ai.ok)updateAI(await ai.json());
}catch{feedback("Impossible de joindre le service vocal. Rechargez la page après son démarrage.",true);}
window.alfredVoice={
  async prepareWake(){
    await cancel("Préparation de la veille.",true);
    el("voice-mode").value="conversation";wakeConversation=true;buttons();
  },
  async receiveWake(value){
    if(!wakeConversation||document.hidden)return;
    const id=++generation;state="processing";
    if(el("voice-auto").checked)followup.arm();
    buttons();
    try{
      const binary=atob(value.audio_base64),data=new Uint8Array(binary.length);
      for(let i=0;i<binary.length;i++)data[i]=binary.charCodeAt(i);
      const headers={"X-Alfred-Session":sessionId,"X-Alfred-Wake-Source":"browser","X-Alfred-Wake-Turn":value.turn};
      if(el("floor").value)headers["X-Alfred-Floor"]=el("floor").value;
      await duckMusicForInteraction();
      const response=await request("/api/conversation/voice",data,"audio/wav",headers);
      await conversationResponse(response,id);
    }catch(error){if(id===generation){await cancel(error.message||"Conversation interrompue.");}}
  },
  stopWakeConversation(){if(wakeConversation){wakeConversation=false;cancel();}},
};
buttons();
