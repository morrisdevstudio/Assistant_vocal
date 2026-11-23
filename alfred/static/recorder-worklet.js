class AlfredRecorder extends AudioWorkletProcessor {
  constructor() {
    super();this.buffer=new Float32Array(1024);this.used=0;this.active=true;
    this.port.onmessage=event=>{
      if(event.data==="flush") {
        this.active=false;
        if(this.used)this.port.postMessage(this.buffer.slice(0,this.used));
        this.used=0;this.port.postMessage("flushed");
      }
    };
  }
  process(inputs, outputs) {
    for(const output of outputs)for(const channel of output)channel.fill(0);
    const channels=inputs[0];
    if(!this.active || !channels?.length)return true;
    for(let i=0;i<channels[0].length;i++) {
      let sum=0;for(const channel of channels)sum+=channel[i];
      this.buffer[this.used++]=sum/channels.length;
      if(this.used===this.buffer.length){this.port.postMessage(this.buffer);this.buffer=new Float32Array(1024);this.used=0;}
    }
    return true;
  }
}
registerProcessor("alfred-recorder",AlfredRecorder);
