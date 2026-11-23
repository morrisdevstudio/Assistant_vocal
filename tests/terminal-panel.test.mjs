import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {readFile} from 'node:fs/promises';

test('les échanges ESP32 alimentent les deux textes sans écraser ensuite le navigateur',async()=>{
  const elements=new Map();
  const element=id=>{
    if(!elements.has(id))elements.set(id,{textContent:'',addEventListener(){}});
    return elements.get(id);
  };
  let exchange={id:'turn-1',revision:1,transcript:'Bonjour Alfred',answer:'',error:null};
  let available=true;
  const timers=[];
  const context=vm.createContext({window:{addEventListener(){},__alfredForceTerminalVisible:true},
    document:{hidden:false,getElementById:element,addEventListener(){},
    querySelector:selector=>selector.includes('voice')?{hidden:false}:null,
    querySelectorAll:()=>[]},
    fetch:async path=>({ok:true,json:async()=>path.endsWith('/conversation')
      ?{available,exchange}:{enabled:false,wake_word:{enabled:false}}}),
    setInterval:fn=>timers.push(fn),setTimeout(){},clearTimeout(){},Date});
  vm.runInContext(await readFile(new URL('../alfred/static/terminal-panel.js',import.meta.url),'utf8'),context);
  const settle=()=>new Promise(resolve=>setImmediate(resolve));
  await settle();
  assert.equal(element('voice-transcript').textContent,'Bonjour Alfred');
  assert.match(element('voice-answer').textContent,/prépare/);
  exchange={...exchange,revision:2,answer:'Bonjour, monsieur.'};
  timers[0]();await settle();
  assert.equal(element('voice-answer').textContent,'Bonjour, monsieur.');
  element('voice-answer').textContent='Réponse depuis le navigateur';
  timers[0]();await settle();
  assert.equal(element('voice-answer').textContent,'Réponse depuis le navigateur');
  exchange={id:'turn-2',revision:0,transcript:'',answer:'',error:null};
  timers[0]();await settle();
  assert.match(element('voice-transcript').textContent,/en cours/);
  assert.match(element('voice-answer').textContent,/prépare/);
  exchange={...exchange,revision:1,error:'Transcription impossible.'};
  timers[0]();await settle();
  assert.equal(element('voice-answer').textContent,'Transcription impossible.');
  assert.doesNotMatch(element('voice-transcript').textContent,/en cours/);
  exchange={id:'turn-3',revision:1,state:'waiting_for_command',transcript:'',answer:'',error:null};
  timers[0]();await settle();
  assert.match(element('voice-answer').textContent,/attend ta demande/);
  exchange={...exchange,revision:2,state:'finished',answer:'Aucune demande après le mot d’appel.'};
  timers[0]();await settle();
  assert.equal(element('voice-answer').textContent,'Aucune demande après le mot d’appel.');
  exchange={id:'turn-4',revision:0,state:'processing',transcript:'',answer:'',error:null};
  timers[0]();await settle();
  available=false;
  timers[0]();await settle();
  assert.equal(element('voice-answer').textContent,'Échange ESP32 interrompu.');
  available=true;
  timers[0]();await settle();
  element('voice-answer').textContent='Nouvelle réponse du navigateur';
  available=false;
  timers[0]();await settle();
  assert.equal(element('voice-answer').textContent,'Nouvelle réponse du navigateur');
});

test('le diagnostic ESP32 affiche le texte et efface le résultat',async()=>{
  const elements=new Map(),timers=[],clears=[],calls=[];
  const element=id=>{
    if(!elements.has(id))elements.set(id,{textContent:'',checked:false,listeners:new Map(),addEventListener(name,fn){this.listeners.set(name,fn);}});
    return elements.get(id);
  };
  let available=false;
  const context=vm.createContext({window:{addEventListener(){},__alfredForceTerminalVisible:true},
    document:{hidden:false,getElementById:element,addEventListener(){},
    querySelector:selector=>selector.includes('voice')?{hidden:false}:null,
    querySelectorAll:()=>[]},URLSearchParams,
    fetch:async(path,options)=>{
      if(options?.method==='POST'){calls.push(path);return {ok:true,json:async()=>({armed:true})};}
      if(path.endsWith('/conversation'))return {ok:true,json:async()=>({available:false})};
      if(path.endsWith('/result'))return {ok:true,json:async()=>({available,armed:!available,
        text:'Est-ce que tu peux raconter une histoire ?',stt_ms:300,input_seconds:2})};
      return {ok:true,json:async()=>({enabled:true,connected:true,phase:'idle',wake_word:{enabled:false}})};
    },setInterval:fn=>timers.push(fn),setTimeout:fn=>clears.push(fn),clearTimeout(){},Date});
  vm.runInContext(await readFile(new URL('../alfred/static/terminal-panel.js',import.meta.url),'utf8'),context);
  const settle=()=>new Promise(resolve=>setImmediate(resolve));await settle();
  await element('terminal-stt-distance').listeners.get('click')();
  assert.equal(calls[0],'/api/terminal/stt-test?start=true');
  available=true;
  // Les boucles vérifient la vue ; ce DOM minimal n'en a pas, donc elles restent actives.
  for(const timer of timers){
    if(timer.length===0)await timer();
    else timer();
  }
  await settle();
  assert.match(element('terminal-stt-result').textContent,/Est-ce que tu peux raconter une histoire \? · 300 ms/);
  clears.at(-1)();assert.equal(element('terminal-stt-result').textContent,'Résultat du test effacé.');
});
