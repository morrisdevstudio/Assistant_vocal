// Recette du contrôleur réel avec DOM/micro/lecteur artificiels, sans aucun accès matériel.
import test from 'node:test';
import assert from 'node:assert/strict';

let scenario=0;
const settle=()=>new Promise(resolve=>setImmediate(resolve));

async function harness(configured=true){
  const originals=new Map();
  const replace=(name,value)=>{originals.set(name,Object.getOwnPropertyDescriptor(globalThis,name));Object.defineProperty(globalThis,name,{value,configurable:true,writable:true});};
  let now=0,nextTimer=0,requests=0,microCalls=0,holdNext=null,nextError=null;
  const timers=new Map(),streams=[],nodes=[],elements=new Map(),calls=[],musicCalls=[],voiceCalls=[];
  class Element{
    constructor(){this.listeners=new Map();this.style={};this.value='';this.textContent='';this.hidden=false;this.disabled=false;this.checked=true;this.paused=true;this.ended=false;this.src='';this.classList={toggle(){}};this.option={};}
    addEventListener(name,callback){const values=this.listeners.get(name)||[];values.push(callback);this.listeners.set(name,values);}
    async emit(name){for(const callback of this.listeners.get(name)||[])await callback({preventDefault(){}});}
    querySelector(){return this.option;}
    pause(){if(!this.paused){this.paused=true;this.emit('pause');}}
    load(){}
    removeAttribute(name){if(name==='src')this.src='';}
    getAttribute(name){return name==='src'?this.src||null:null;}
    async play(){this.paused=false;this.ended=false;await this.emit('play');}
  }
  const element=id=>{if(!elements.has(id))elements.set(id,new Element());return elements.get(id);};
  const doc=new Element();doc.hidden=false;doc.getElementById=element;
  const win=new Element();win.isSecureContext=true;
  const makeStream=()=>{const track={stopped:false,stop(){this.stopped=true;},addEventListener(){}};const stream={getTracks:()=>[track],getAudioTracks:()=>[track],track};streams.push(stream);return stream;};
  class Context{
    constructor(){this.sampleRate=48000;this.state='running';this.destination={};this.audioWorklet={addModule:async()=>{}};}
    createMediaStreamSource(){return {connect(){},disconnect(){}};}
    async resume(){}
    async close(){this.state='closed';}
  }
  class Worklet{
    constructor(){this.port={onmessage:null,postMessage:value=>{if(value==='flush')this.port.onmessage({data:'flushed'});}};nodes.push(this);}
    connect(){}disconnect(){}
  }
  const responseEvents=[{type:'transcript',text:'Bonjour',stt_ms:1,input_seconds:0.2},
    {type:'delta',text:'À votre service.'},{type:'answer',text:'À votre service.'},
    {type:'done',needs_reply:true,audio_base64:btoa('synthetic-audio'),timings:{stt_ms:1,llm_ms:2,tts_ms:3}}];
  replace('document',doc);replace('window',win);replace('performance',{now:()=>now});
  replace('navigator',{mediaDevices:{getUserMedia:async()=>{microCalls++;if(nextError){const error=nextError;nextError=null;throw error;}if(holdNext){const wait=holdNext;holdNext=null;await wait;}return makeStream();}}});
  replace('AudioContext',Context);replace('AudioWorkletNode',Worklet);
  replace('setTimeout',(callback,delay)=>{const id=++nextTimer;timers.set(id,{callback,at:now+delay,period:0});return id;});
  replace('clearTimeout',id=>timers.delete(id));
  replace('setInterval',(callback,delay)=>{const id=++nextTimer;timers.set(id,{callback,at:now+delay,period:delay});return id;});
  replace('clearInterval',id=>timers.delete(id));
  replace('fetch',async(path,options)=>{
    if(path==='/api/voice/status')return Response.json({stt_available:true,tts_available:true});
    if(path==='/api/ai/config')return Response.json({configured});
    if(path==='/api/conversation/voice'||path==='/api/conversation/text'){requests++;calls.push({path,options});return new Response(responseEvents.map(event=>JSON.stringify(event)+'\n').join(''));}
    if(path==='/api/voice/speak')return new Response(new Blob(['synthetic-audio']),{headers:{'X-TTS-Ms':'1'}});
    if(path==='/api/voice/config'){const body=JSON.parse(options.body);voiceCalls.push(body);
      return Response.json({stt_available:true,tts_available:true,tts_voice_id:body.voice});}
    if(path==='/api/conversation/reset')return Response.json({reset:true});
    if(path==='/api/voice/turn'){calls.push({path,options});return Response.json({input_seconds:1,
      text:'Est-ce que',reply_text:'Test audio.',audio_base64:null,timings:{stt_ms:300,tts_ms:0}});}
    if(path==='/api/music/duck'){musicCalls.push({path,options});return Response.json({ducked:true,owned:true});}
    if(path==='/api/music/restore'){musicCalls.push({path,options});return Response.json({ducked:false,restored:true});}
    throw new Error('Requête inattendue : '+path);
  });
  element('voice-mode').value='conversation';
  try{await import(new URL(`../alfred/static/voice-controller.js?scenario=${++scenario}`,import.meta.url));await settle();}
  catch(error){for(const [name,descriptor] of originals){if(descriptor)Object.defineProperty(globalThis,name,descriptor);else delete globalThis[name];}throw error;}
  async function advance(ms){
    now+=ms;
    for(const [id,timer] of [...timers]){
      if(!timers.has(id)||timer.at>now)continue;
      if(timer.period)timer.at=now+timer.period;else timers.delete(id);
      timer.callback();
    }
    await settle();
  }
  async function speech(){
    for(let i=0;i<12;i++){now+=20;nodes.at(-1).port.onmessage({data:new Float32Array(960).fill(0.05)});}
    await advance(1000);await settle();
  }
  async function endAudio(){const media=element('voice-reply');media.paused=true;media.ended=true;await media.emit('pause');await media.emit('ended');await settle();}
  return {element,doc,win,responseEvents,streams,calls,musicCalls,voiceCalls,get requests(){return requests;},get microCalls(){return microCalls;},advance,speech,endAudio,
    async start(){await element('voice-record').emit('click');await settle();},
    holdNext(){let resolve;holdNext=new Promise(done=>{resolve=done;});return resolve;},
    denyNext(){nextError=Object.assign(new Error('Permission refusée'),{name:'NotAllowedError'});},
    async cleanup(){await win.emit('pagehide');await settle();for(const [name,descriptor] of originals){if(descriptor)Object.defineProperty(globalThis,name,descriptor);else delete globalThis[name];}}
  };
}

test('micro fermé pendant la réponse, reprise après sa fin, silence sans second appel IA',async()=>{
  const h=await harness();try{
    await h.start();await h.speech();
    assert.equal(h.requests,1);assert.equal(h.microCalls,1);assert.equal(h.streams[0].track.stopped,true);
    await h.advance(20000);assert.equal(h.microCalls,1);
    await h.endAudio();assert.equal(h.microCalls,2);assert.equal(h.streams[1].track.stopped,false);
    await h.advance(7999);assert.equal(h.streams[1].track.stopped,false);
    await h.advance(2);assert.equal(h.streams[1].track.stopped,true);assert.equal(h.requests,1);
    assert.match(h.element('voice-feedback').textContent,/8 secondes/);
    await h.endAudio();assert.equal(h.microCalls,2);
  }finally{await h.cleanup();}
});

test('une commande terminée ferme le dialogue et restaure la musique',async()=>{
  const h=await harness();try{
    h.responseEvents.at(-1).needs_reply=false;
    await h.start();await h.speech();await h.endAudio();
    await h.advance(9000);
    assert.equal(h.microCalls,1);assert.equal(h.requests,1);
    assert.deepEqual(h.musicCalls.map(call=>call.path),['/api/music/duck','/api/music/restore']);
  }finally{await h.cleanup();}
});

test('la musique est réduite pendant la conversation et restaurée une seule fois à sa fin',async()=>{
  const h=await harness();try{
    await h.start();await h.speech();
    assert.deepEqual(h.musicCalls.map(call=>call.path),['/api/music/duck']);
    await h.endAudio();
    assert.deepEqual(h.musicCalls.map(call=>call.path),['/api/music/duck']);
    await h.element('voice-cancel').emit('click');await settle();
    assert.deepEqual(h.musicCalls.map(call=>call.path),['/api/music/duck','/api/music/restore']);
    assert.equal(JSON.parse(h.musicCalls[0].options.body).session_id,
                 JSON.parse(h.musicCalls[1].options.body).session_id);
  }finally{await h.cleanup();}
});

test('le test audio affiche la transcription sans IA ni reprise automatique',async()=>{
  const h=await harness(false);try{
    h.element('voice-mode').value='audio-test';await h.element('voice-mode').emit('change');
    await h.start();await h.speech();await h.element('voice-record').emit('click');await settle();
    assert.equal(h.calls.length,1);assert.equal(h.calls[0].path,'/api/voice/turn');
    assert.equal(h.requests,0);assert.deepEqual(h.musicCalls,[]);
    assert.equal(h.element('voice-transcript').textContent,'Est-ce que');
    assert.match(h.element('voice-timings').textContent,/300 ms/);
    assert.equal(h.element('voice-reply').paused,true);
    assert.equal(h.streams[0].track.stopped,true);
    await h.advance(9000);assert.equal(h.microCalls,1);
  }finally{await h.cleanup();}
});

test('minuteurs accessibles sans clé IA, étage transmis au clavier et au micro',async()=>{
  const h=await harness(false);try{
    h.element('floor').value='etage1';
    assert.equal(h.element('voice-mode').option.disabled,false);
    assert.equal(h.element('chat-send').disabled,false);
    h.element('chat-text').value='mets un minuteur de huit minutes';
    await h.element('chat-form').emit('submit');await h.endAudio();
    assert.equal(JSON.parse(h.calls[0].options.body).floor_id,'etage1');
    await h.start();await h.speech();
    assert.equal(h.calls[1].options.headers['X-Alfred-Floor'],'etage1');
  }finally{await h.cleanup();}
});
test('une nouvelle phrase poursuit le même dialogue et donne une seule réponse',async()=>{
  const h=await harness();try{
    await h.start();await h.speech();await h.endAudio();
    await h.speech();assert.equal(h.requests,2);assert.equal(h.streams[1].track.stopped,true);
    assert.equal(h.calls[0].options.headers['X-Alfred-Session'],h.calls[1].options.headers['X-Alfred-Session']);
    await h.endAudio();assert.equal(h.microCalls,3);
    await h.element('voice-cancel').emit('click');assert.equal(h.streams[2].track.stopped,true);
    await h.advance(10000);assert.equal(h.requests,2);assert.equal(h.microCalls,3);
  }finally{await h.cleanup();}
});
test('arrêter une demande de micro encore en attente ferme le flux arrivé tardivement',async()=>{
  const h=await harness();try{
    await h.start();await h.speech();const release=h.holdNext();await h.endAudio();
    assert.equal(h.microCalls,2);
    await h.element('voice-cancel').emit('click');release();await settle();
    assert.equal(h.streams[1].track.stopped,true);
    await h.advance(10000);assert.equal(h.microCalls,2);assert.equal(h.requests,1);
  }finally{await h.cleanup();}
});
test('une question écrite et un échantillon de voix ne demandent pas de microphone',async()=>{
  const h=await harness();try{
    h.element('chat-text').value='Présente-toi';await h.element('chat-form').emit('submit');await h.endAudio();
    assert.equal(h.requests,1);assert.equal(h.microCalls,0);
    await h.element('voice-sample').emit('click');await h.endAudio();assert.equal(h.microCalls,0);
  }finally{await h.cleanup();}
});
for(const voice of ['phonon-arnaud-cpu','phonon-lucien-cpu','phonon-alfred-cpu','phonon-dumby-cpu'])test(`le choix ${voice} est envoyé au service et reste disponible pour l’écoute`,async()=>{
  const h=await harness();try{
    h.element('voice-choice').value=voice;await h.element('voice-choice').emit('change');await settle();
    assert.deepEqual(h.voiceCalls,[{voice}]);
    assert.equal(h.element('voice-choice').value,voice);
    assert.equal(h.element('voice-sample').disabled,false);
    assert.equal(h.microCalls,0);
  }finally{await h.cleanup();}
});
test('l’option désactivée ou un onglet caché coupe la reprise',async()=>{
  const h=await harness();try{
    await h.start();await h.speech();h.element('voice-auto').checked=false;await h.element('voice-auto').emit('change');await h.endAudio();
    assert.equal(h.microCalls,1);
    h.element('voice-auto').checked=true;await h.start();h.doc.hidden=true;await h.doc.emit('visibilitychange');
    assert.equal(h.streams.at(-1).track.stopped,true);await h.advance(10000);assert.equal(h.microCalls,2);
  }finally{await h.cleanup();}
});
test('réécouter un enregistrement pendant l’attente ferme le micro',async()=>{
  const h=await harness();try{
    await h.start();await h.speech();await h.endAudio();
    assert.equal(h.streams[1].track.stopped,false);
    await h.element('voice-preview').play();await settle();assert.equal(h.streams[1].track.stopped,true);
    await h.advance(10000);assert.equal(h.requests,1);
  }finally{await h.cleanup();}
});
test('une phrase près de la limite finit après huit secondes sans être coupée',async()=>{
  const h=await harness();try{
    await h.start();await h.speech();await h.endAudio();await h.advance(7900);
    await h.speech();assert.equal(h.requests,2);assert.equal(h.streams[1].track.stopped,true);
  }finally{await h.cleanup();}
});
test('un refus du micro à la reprise ne crée pas de boucle ou d’appel IA',async()=>{
  const h=await harness();try{
    await h.start();await h.speech();h.denyNext();await h.endAudio();
    assert.match(h.element('voice-feedback').textContent,/refusé/);
    await h.advance(20000);assert.equal(h.microCalls,2);assert.equal(h.requests,1);
  }finally{await h.cleanup();}
});


test('un réveil navigateur réutilise la conversation, transmet le ticket et garde la reprise',async()=>{
  const h=await harness();try{
    await h.win.alfredVoice.prepareWake();
    assert.equal(h.microCalls,0);
    await h.win.alfredVoice.receiveWake({turn:'unique-wake-ticket',audio_base64:btoa('synthetic-audio')});
    assert.equal(h.requests,1);
    assert.equal(h.calls[0].options.headers['X-Alfred-Wake-Turn'],'unique-wake-ticket');
    assert.equal(h.calls[0].options.headers['X-Alfred-Wake-Source'],'browser');
    assert.equal(h.microCalls,0);
    await h.endAudio();
    assert.equal(h.microCalls,1);
    await h.speech();
    assert.equal(h.requests,2);
  }finally{await h.cleanup();}
});

test('mot seul ouvre six secondes même sans reprise automatique, puis silence sans nouvel envoi',async()=>{
  const h=await harness();try{
    await h.win.alfredVoice.prepareWake();
    h.element('voice-auto').checked=false;
    h.responseEvents.splice(0,h.responseEvents.length,{type:'done',mode:'wake_empty',text:'',audio_base64:'',timings:{stt_ms:1,llm_ms:0,tts_ms:0}});
    await h.win.alfredVoice.receiveWake({turn:'wake-alone',audio_base64:btoa('synthetic-audio')});
    assert.equal(h.microCalls,1);
    assert.equal(h.streams[0].track.stopped,false);
    await h.advance(6001);
    assert.equal(h.streams[0].track.stopped,true);
    assert.equal(h.requests,1);
  }finally{await h.cleanup();}
});
