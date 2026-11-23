import test from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";

let counter=0;
async function harness(){
  const saved=new Map(),elements=new Map(),calls=[],streams=[],sockets=[],nodes=[];
  function replace(key,value){saved.set(key,Object.getOwnPropertyDescriptor(globalThis,key));Object.defineProperty(globalThis,key,{value,configurable:true,writable:true});}
  class Element{
    constructor(){this.listeners=new Map();this.value="";this.textContent="";this.children=[];this.disabled=false;this.hidden=false;}
    addEventListener(name,fn){const listeners=this.listeners.get(name)||[];listeners.push(fn);this.listeners.set(name,listeners);}
    async emit(name){for(const fn of this.listeners.get(name)||[])await fn({preventDefault(){}});}
    replaceChildren(){this.children=[];}
    append(value){this.children.push(value);}
  }
  const el=id=>{if(!elements.has(id))elements.set(id,new Element());return elements.get(id);};
  const doc=new Element();doc.hidden=false;doc.getElementById=el;doc.createElement=()=>new Element();
  const win=new Element();win.isSecureContext=true;win.alfredVoice={prepareWake:async()=>{},stopWakeConversation(){},receiveWake:async()=>{}};
  const value={engine:"stt",model:"jarvis.onnx",threshold:.5,phrase:"Alfy",variants:["Alfi"]};
  const snapshot={settings:{browser:{...value},esp32:{...value,engine:"openwakeword"}},models:[{id:"jarvis.onnx",label:"Jarvis",phrase:"Jarvis"}],owner:null,busy:false};
  let allow=null;
  const makeStream=()=>{const track={stopped:false,stop(){this.stopped=true;},addEventListener(){}};
    const stream={getTracks:()=>[track],track};streams.push(stream);return stream;};
  class Context{
    constructor(){this.sampleRate=48000;this.audioWorklet={addModule:async()=>{}};}
    createMediaStreamSource(){return {connect(){},disconnect(){}};}
    async close(){this.closed=true;}
    async resume(){}
  }
  class Worklet{constructor(){this.port={};nodes.push(this);}connect(){}disconnect(){}}
  class Socket{
    static OPEN=1;
    constructor(){this.readyState=1;this.bufferedAmount=0;this.sent=[];sockets.push(this);}
    send(value){this.sent.push(value);}
    close(){this.readyState=3;this.onclose?.();}
    async receive(value){await this.onmessage({data:JSON.stringify(value)});}
  }
  replace("document",doc);replace("window",win);replace("location",{href:"http://localhost/#voice",protocol:"http:"});
  replace("navigator",{mediaDevices:{getUserMedia:async()=>allow?allow:makeStream()}});
  replace("AudioContext",Context);replace("AudioWorkletNode",Worklet);replace("WebSocket",Socket);
  replace("setInterval",()=>1);replace("clearInterval",()=>{});
  replace("fetch",async(path,options)=>{
    calls.push({path,options});
    if(options.method==="PUT")snapshot.settings[path.split("/").at(-1)]=JSON.parse(options.body);
    return Response.json(snapshot);
  });
  let source=await readFile(new URL("../alfred/static/wake-panel.js",import.meta.url),"utf8");
  source=source.replace('"./wake-audio.mjs"',JSON.stringify(new URL("../alfred/static/wake-audio.mjs",import.meta.url).href));
  await import(`data:text/javascript;base64,${Buffer.from(source).toString("base64")}#${counter++}`);
  return {el,doc,win,calls,streams,sockets,nodes,
    holdPermission(){let resolve;allow=new Promise(done=>resolve=done);return ()=>resolve(makeStream());},
    async cleanup(){await win.emit("pagehide");for(const [key,descriptor] of saved){if(descriptor)Object.defineProperty(globalThis,key,descriptor);else delete globalThis[key];}}
  };
}

test("réglages STT modifiables, modèle explicite et aucun micro ouvert au chargement",async()=>{
  const h=await harness();try{
    assert.equal(h.streams.length,0);
    assert.equal(h.el("wake-browser-phrase").value,"Alfy");
    assert.equal(h.el("wake-browser-variants").value,"Alfi");
    assert.equal(h.el("wake-browser-stt").hidden,false);
    h.el("wake-browser-engine").value="openwakeword";
    await h.el("wake-browser-engine").emit("change");
    assert.equal(h.el("wake-browser-stt").hidden,true);
    assert.match(h.el("wake-browser-model").children[0].textContent,/Jarvis/);
    h.el("wake-browser-engine").value="stt";
    await h.el("wake-browser-engine").emit("change");
    h.el("wake-browser-phrase").value="Mon Alfred";
    await h.el("wake-browser-save").emit("click");
    const call=h.calls.find(value=>value.options.method==="PUT");
    assert.equal(JSON.parse(call.options.body).phrase,"Mon Alfred");
    assert.equal(JSON.parse(call.options.body).model,"jarvis.onnx");
  }finally{await h.cleanup();}
});

test("veille transmet du PCM puis ferme micro et canal quand la page est cachée",async()=>{
  const h=await harness();try{
    await h.el("wake-browser-start").emit("click");
    await h.sockets[0].receive({type:"ready"});
    h.nodes[0].port.onmessage({data:new Float32Array(480).fill(.2)});
    assert.equal(h.sockets[0].sent[0].byteLength,320);
    h.doc.hidden=true;await h.doc.emit("visibilitychange");
    assert.equal(h.streams[0].track.stopped,true);
    assert.equal(h.sockets[0].readyState,3);
    assert.equal(h.el("wake-browser-stop").disabled,true);
  }finally{await h.cleanup();}
});

test("arrêt pendant la permission micro élimine le flux tardif sans ouvrir de WebSocket",async()=>{
  const h=await harness();try{
    const release=h.holdPermission();
    const starting=h.el("wake-browser-start").emit("click");
    await new Promise(resolve=>setImmediate(resolve));
    await h.el("wake-browser-stop").emit("click");
    release();await starting;
    assert.equal(h.streams[0].track.stopped,true);
    assert.equal(h.sockets.length,0);
  }finally{await h.cleanup();}
});
