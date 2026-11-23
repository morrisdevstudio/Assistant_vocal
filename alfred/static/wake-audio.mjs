// Rééchantillonnage continu : conserver les fractions entre paquets du worklet.
export class PCMResampler {
  constructor(rate){
    if(!Number.isFinite(rate)||rate<16000||rate>96000)throw new Error("Fréquence micro incompatible.");
    this.ratio=rate/16000;this.weight=0;this.sum=0;
  }
  push(input){
    const samples=[];
    for(const raw of input){
      const sample=Number.isFinite(raw)?Math.max(-1,Math.min(1,raw)):0;
      let left=1;
      while(left>1e-9){
        const take=Math.min(left,this.ratio-this.weight);
        this.sum+=sample*take;this.weight+=take;left-=take;
        if(this.weight>=this.ratio-1e-9){
          const value=this.sum/this.ratio;
          samples.push(Math.round(value*(value<0?32768:32767)));
          this.sum=this.weight=0;
        }
      }
    }
    const data=new ArrayBuffer(samples.length*2),view=new DataView(data);
    samples.forEach((value,index)=>view.setInt16(index*2,value,true));
    return data;
  }
}
