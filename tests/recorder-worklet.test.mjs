import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import fs from 'node:fs';

test('le worklet conserve les échantillons, reste silencieux en sortie et vide la dernière trame',()=>{
  let Recorder;const messages=[];
  const context=vm.createContext({Float32Array,AudioWorkletProcessor:class{constructor(){this.port={postMessage:value=>messages.push(value)};}},
    registerProcessor:(name,value)=>{assert.equal(name,'alfred-recorder');Recorder=value;}});
  vm.runInContext(fs.readFileSync(new URL('../alfred/static/recorder-worklet.js',import.meta.url),'utf8'),context);
  const recorder=new Recorder();const output=new Float32Array(128).fill(1);
  for(let i=0;i<9;i++)recorder.process([[new Float32Array(128).fill(0.2)]],[[output]]);
  assert.equal(messages[0].length,1024);assert.ok(Math.abs(messages[0][0]-0.2)<1e-6);
  assert.ok(output.every(sample=>sample===0));
  recorder.port.onmessage({data:'flush'});
  assert.equal(messages[1].length,128);assert.equal(messages[2],'flushed');
  recorder.process([[new Float32Array(128).fill(0.8)]],[[output]]);
  assert.equal(messages.length,3);
});
