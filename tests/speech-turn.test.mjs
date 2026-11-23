import test from 'node:test';
import assert from 'node:assert/strict';
import {SpeechTurn,FollowupPolicy} from '../alfred/static/speech-turn.mjs';

const RATE=48000;
const chunk=(level=0)=>new Float32Array(960).fill(level); // 20 ms
function speak(gate,start,duration,level=0.05){let result;for(let t=start+20;t<=start+duration;t+=20)result=gate.push(chunk(level),t);return result;}

test('huit secondes de silence ferment sans audio à envoyer',()=>{
  const gate=new SpeechTurn({sampleRate:RATE,deadline:8000});
  assert.equal(gate.poll(7999).done,false);
  assert.deepEqual(gate.poll(8000),{done:true,reason:'empty',hasSpeech:false,remainingMs:0});
  assert.deepEqual(gate.audioChunks(),[]);
});
test('une phrase commencée avant huit secondes peut finir après',()=>{
  const gate=new SpeechTurn({sampleRate:RATE,deadline:8000});
  speak(gate,7900,600);
  assert.equal(gate.hasSpeech,true);
  assert.equal(gate.poll(8500).done,false);
  assert.equal(gate.poll(9499).done,false);
  assert.equal(gate.poll(9500).reason,'silence');
  assert.ok(gate.audioChunks().length);
});
test('un départ très près de la limite conserve le premier mot',()=>{
  const gate=new SpeechTurn({sampleRate:RATE,deadline:8000});
  assert.equal(speak(gate,7980,20).done,false);
  assert.equal(gate.poll(8000).done,false);
  speak(gate,8000,160);
  assert.equal(gate.hasSpeech,true);
  assert.equal(gate.poll(8160).done,false);
});
test('une voix qui commence après la fenêtre ne réactive pas la capture',()=>{
  const gate=new SpeechTurn({sampleRate:RATE,deadline:8000});
  assert.equal(speak(gate,8001,200).hasSpeech,false);
  assert.equal(gate.done,true);
  assert.deepEqual(gate.audioChunks(),[]);
});
test('les clics brefs ne suffisent pas à ouvrir un tour',()=>{
  const gate=new SpeechTurn({sampleRate:RATE,deadline:8000});
  speak(gate,2000,60);
  gate.push(chunk(),2080);
  assert.equal(gate.hasSpeech,false);
  assert.equal(gate.poll(8000).reason,'empty');
});
test('pré-enregistrement borné et pas de longue attente jointe à la phrase',()=>{
  const gate=new SpeechTurn({sampleRate:RATE,deadline:8000});
  for(let t=20;t<=7000;t+=20)gate.push(chunk(),t);
  assert.ok(gate.preFrames<=RATE/4);
  speak(gate,7000,300);
  const total=gate.audioChunks().reduce((sum,c)=>sum+c.length,0);
  assert.ok(total<RATE);
  assert.ok(total>=RATE*0.3);
});
test('la phrase ne dépasse pas trente secondes de PCM',()=>{
  const gate=new SpeechTurn({sampleRate:RATE,deadline:8000});
  speak(gate,0,31000);
  assert.equal(gate.reason,'limit');
  assert.equal(gate.audioChunks().reduce((sum,c)=>sum+c.length,0),RATE*30);
});
test('un même résultat de fin est stable et ne capture plus de données',()=>{
  const gate=new SpeechTurn({sampleRate:RATE,deadline:8000});
  speak(gate,0,300);gate.poll(1300);
  const frames=gate.frames;
  gate.push(chunk(0.1),2000);gate.poll(5000);
  assert.equal(gate.frames,frames);
  assert.equal(gate.reason,'silence');
});
test('le compte à rebours commence à la fin de réponse, une seule fois',()=>{
  const policy=new FollowupPolicy();policy.arm();policy.expectReply(3);
  assert.deepEqual(policy.ended(3,12000,{enabled:true,conversation:true,visible:true}),{generation:3,deadline:20000});
  assert.equal(policy.ended(3,13000,{enabled:true,conversation:true,visible:true}),null);
});
test('un événement ancien ne consomme pas la réponse courante',()=>{
  const policy=new FollowupPolicy();policy.arm();policy.expectReply(5);
  assert.equal(policy.ended(4,0,{enabled:true,conversation:true,visible:true}),null);
  assert.ok(policy.ended(5,20,{enabled:true,conversation:true,visible:true}));
});
test('arrêt, message écrit, échantillon, onglet caché et option désactivée ne réouvrent pas',()=>{
  for(const options of [{enabled:false,conversation:true,visible:true},{enabled:true,conversation:false,visible:true},{enabled:true,conversation:true,visible:false}]){
    const policy=new FollowupPolicy();policy.arm();policy.expectReply(1);
    assert.equal(policy.ended(1,0,options),null);
  }
  const stopped=new FollowupPolicy();stopped.arm();stopped.expectReply(1);stopped.stop();
  assert.equal(stopped.ended(1,0,{enabled:true,conversation:true,visible:true}),null);
  const unarmed=new FollowupPolicy();unarmed.expectReply(1);
  assert.equal(unarmed.ended(1,0,{enabled:true,conversation:true,visible:true}),null);
});
