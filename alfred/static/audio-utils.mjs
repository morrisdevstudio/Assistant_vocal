export function encodeWav(chunks, sampleRate) {
  if (!Number.isInteger(sampleRate) || sampleRate < 8000 || sampleRate > 96000) throw new Error("Fréquence audio non prise en charge.");
  const count = chunks.reduce((sum, chunk) => sum + chunk.length, 0);
  if (!count || count > sampleRate * 30) throw new Error("L’enregistrement doit durer entre zéro et 30 secondes.");
  const buffer = new ArrayBuffer(44 + count * 2);
  const view = new DataView(buffer);
  const string = (at, value) => { for (let i=0;i<value.length;i++) view.setUint8(at+i,value.charCodeAt(i)); };
  string(0,"RIFF");view.setUint32(4,36+count*2,true);string(8,"WAVE");string(12,"fmt ");
  view.setUint32(16,16,true);view.setUint16(20,1,true);view.setUint16(22,1,true);
  view.setUint32(24,sampleRate,true);view.setUint32(28,sampleRate*2,true);
  view.setUint16(32,2,true);view.setUint16(34,16,true);string(36,"data");view.setUint32(40,count*2,true);
  let offset=44;
  for (const chunk of chunks) for (const input of chunk) {
    const sample=Number.isFinite(input)?Math.max(-1,Math.min(1,input)):0;
    view.setInt16(offset,sample<0?Math.round(sample*32768):Math.round(sample*32767),true);offset+=2;
  }
  return buffer;
}

export function decodeAudioBase64(value) {
  const binary=atob(value);
  const bytes=new Uint8Array(binary.length);
  for (let i=0;i<binary.length;i++) bytes[i]=binary.charCodeAt(i);
  return new Blob([bytes],{type:"audio/wav"});
}
