import test from 'node:test';
import assert from 'node:assert/strict';
import { encodeWav } from '../alfred/static/audio-utils.mjs';

test('WAV mono PCM16 avec en-tête correct et écrêtage des échantillons',()=>{
  const buffer=encodeWav([new Float32Array([-2,-0.5,0]),new Float32Array([0.5,2,NaN])],48000);
  const view=new DataView(buffer);
  assert.equal(new TextDecoder().decode(buffer.slice(0,4)),'RIFF');
  assert.equal(view.getUint32(24,true),48000);
  assert.equal(view.getUint16(22,true),1);
  assert.equal(view.getUint16(34,true),16);
  assert.equal(view.getUint32(40,true),12);
  assert.equal(view.getInt16(44,true),-32768);
  assert.equal(view.getInt16(52,true),32767);
  assert.equal(view.getInt16(54,true),0);
});
test('refus des prises vides, trop longues et des fréquences invalides',()=>{
  assert.throws(()=>encodeWav([],48000));
  assert.throws(()=>encodeWav([new Float32Array(8000*30+1)],8000));
  assert.throws(()=>encodeWav([new Float32Array(10)],192000));
});
