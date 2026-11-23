import test from "node:test";
import assert from "node:assert/strict";
import {PCMResampler} from "../alfred/static/wake-audio.mjs";

for(const rate of [16000,44100,48000]){
  test(`rééchantillonnage ${rate} Hz continu et indépendant des paquets`,()=>{
    const input=Float32Array.from({length:rate},(_,i)=>Math.sin(i/100)*.3);
    const whole=new Uint8Array(new PCMResampler(rate).push(input));
    const stream=new PCMResampler(rate),parts=[];
    for(let at=0;at<input.length;at+=137)parts.push(new Uint8Array(stream.push(input.subarray(at,at+137))));
    const split=new Uint8Array(parts.reduce((n,p)=>n+p.length,0));let at=0;
    for(const part of parts){split.set(part,at);at+=part.length;}
    assert.equal(whole.length,32000);
    assert.deepEqual(split,whole);
  });
}
test("PCM borné, little endian et valeurs non finies silencieuses",()=>{
  const result=new DataView(new PCMResampler(16000).push([NaN,Infinity,-2,2]));
  assert.deepEqual([0,1,2,3].map(i=>result.getInt16(i*2,true)),[0,0,-32768,32767]);
});
