// Détection locale par énergie : ce n'est ni une identité vocale ni un filtre de télévision.
export class SpeechTurn {
  constructor({sampleRate, deadline, minSpeechMs=160, silenceMs=1000, preRollMs=250, maxSeconds=30}) {
    this.sampleRate=sampleRate;this.deadline=deadline;this.minSpeech=sampleRate*minSpeechMs/1000;
    this.silenceMs=silenceMs;this.preRollFrames=Math.ceil(sampleRate*preRollMs/1000);
    this.maxFrames=Math.floor(sampleRate*maxSeconds);this.graceMs=minSpeechMs+100;
    this.noise=0.001;this.run=0;this.candidateAt=null;this.hasSpeech=false;this.lastVoice=null;
    this.preRoll=[];this.preFrames=0;this.chunks=[];this.frames=0;this.done=false;this.reason=null;
  }
  append(samples) {
    const count=Math.min(samples.length,this.maxFrames-this.frames);
    if(count>0){this.chunks.push(samples.slice(0,count));this.frames+=count;}
  }
  push(samples,now) {
    if(this.done)return this.snapshot(now);
    if(!samples.length)return this.poll(now);
    const duration=samples.length*1000/this.sampleRate;
    let energy=0;for(const sample of samples)energy+=sample*sample;
    const rms=Math.sqrt(energy/samples.length);
    const voiced=rms>=Math.max(0.006,this.noise*3);
    const alreadyStarted=this.hasSpeech;
    if(voiced){
      if(!this.run)this.candidateAt=now-duration;
      this.run+=samples.length;
    }else{
      this.run=0;this.candidateAt=null;
      if(!this.hasSpeech)this.noise=0.98*this.noise+0.02*Math.min(rms,0.02);
    }
    if(!this.hasSpeech){
      this.preRoll.push(samples.slice());this.preFrames+=samples.length;
      while(this.preFrames>this.preRollFrames){
        const remove=Math.min(this.preFrames-this.preRollFrames,this.preRoll[0].length);
        if(remove===this.preRoll[0].length)this.preRoll.shift();
        else this.preRoll[0]=this.preRoll[0].slice(remove);
        this.preFrames-=remove;
      }
      if(this.run>=this.minSpeech && this.candidateAt<=this.deadline && now<=this.deadline+this.graceMs){
        this.hasSpeech=true;this.lastVoice=now;
        for(const chunk of this.preRoll)this.append(chunk);
        this.preRoll=[];this.preFrames=0;
      }
    }else this.append(samples);
    if(this.hasSpeech && voiced)this.lastVoice=now;
    const result=this.poll(now);
    return {...result,started:!alreadyStarted && this.hasSpeech};
  }
  poll(now) {
    if(!this.done){
      if(this.frames>=this.maxFrames)this.finish("limit");
      else if(this.hasSpeech && now-this.lastVoice>=this.silenceMs)this.finish("silence");
      else if(!this.hasSpeech && now>=this.deadline){
        const pending=this.run>0 && this.candidateAt<=this.deadline && now<this.deadline+this.graceMs;
        if(!pending)this.finish("empty");
      }
    }
    return this.snapshot(now);
  }
  finish(reason="manual") {
    if(!this.done){this.done=true;this.reason=this.hasSpeech?reason:"empty";this.preRoll=[];this.preFrames=0;}
  }
  snapshot(now) {
    return {done:this.done,reason:this.reason,hasSpeech:this.hasSpeech,
            remainingMs:this.hasSpeech?null:Math.max(0,this.deadline-now)};
  }
  audioChunks(){return this.hasSpeech?this.chunks:[];}
}

// Une réponse n'autorise qu'une seule reprise ; les relectures manuelles ne réarment rien.
export class FollowupPolicy {
  constructor(){this.armed=false;this.pending=null;}
  arm(){this.armed=true;}
  stop(){this.armed=false;this.pending=null;}
  expectReply(generation){this.pending=this.armed?generation:null;}
  ended(generation,now,{enabled,conversation,visible}){
    const matches=this.pending===generation;
    if(!matches)return null;
    this.pending=null;
    if(!this.armed || !enabled || !conversation || !visible)return null;
    return {generation,deadline:now+8000};
  }
}
