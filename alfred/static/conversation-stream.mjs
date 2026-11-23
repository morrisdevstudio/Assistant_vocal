export async function readConversation(response,onEvent){
  if(!response.ok){const body=await response.json();throw new Error(typeof body.detail==="string"?body.detail:"Conversation indisponible.");}
  const reader=response.body.getReader();const decoder=new TextDecoder();let pending="",done=false;
  function consume(line){
    if(!line.trim())return;
    const event=JSON.parse(line);
    if(event.type==="error")throw new Error(event.message);
    if(event.type==="done")done=true;
    onEvent(event);
  }
  try{
    while(true){const chunk=await reader.read();if(chunk.done)break;pending+=decoder.decode(chunk.value,{stream:true});
      let newline;while((newline=pending.indexOf("\n"))>=0){consume(pending.slice(0,newline));pending=pending.slice(newline+1);}}
    pending+=decoder.decode();if(pending.trim())consume(pending);
    if(!done)throw new Error("La réponse a été interrompue avant la fin.");
  }finally{await reader.cancel().catch(()=>{});reader.releaseLock();}
}
