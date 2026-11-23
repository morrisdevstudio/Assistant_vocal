import test from 'node:test';
import assert from 'node:assert/strict';
import {readConversation} from '../alfred/static/conversation-stream.mjs';

test('flux découpé au milieu des lignes et caractères français',async()=>{
  const bytes=new TextEncoder().encode('{"type":"delta","text":"À votre service"}\n{"type":"done","audio_base64":""}\n');
  let i=0;const stream=new ReadableStream({pull(controller){if(i>=bytes.length){controller.close();return;}controller.enqueue(bytes.slice(i,i+1));i++;}});
  const events=[];await readConversation(new Response(stream),event=>events.push(event));
  assert.equal(events[0].text,'À votre service');assert.equal(events[1].type,'done');
});
test('refuse une réponse coupée sans événement de fin',async()=>{
  await assert.rejects(readConversation(new Response('{"type":"delta","text":"Début"}\n'),()=>{}),/interrompue/);
});
test('remonte les erreurs sans les transformer en succès',async()=>{
  await assert.rejects(readConversation(new Response('{"type":"error","message":"Quota atteint"}\n'),()=>{}),/Quota atteint/);
});
