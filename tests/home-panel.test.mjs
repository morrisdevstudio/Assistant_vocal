import test from 'node:test';
import assert from 'node:assert/strict';

const settle=()=>new Promise(resolve=>setImmediate(resolve));

class Node{
  constructor(tag){this.tagName=tag;this.children=[];this.attributes={};this.listeners=new Map();
    this.classList={toggle(){}};this.dataset={};this.options=[];this.value='';this.textContent='';
    this.hidden=false;this.disabled=false;this.checked=false;this.open=false;this.title='';}
  addEventListener(name,callback){const values=this.listeners.get(name)||[];values.push(callback);this.listeners.set(name,values);}
  async emit(name,event={preventDefault(){}}){for(const callback of this.listeners.get(name)||[])await callback(event);}
  append(...items){for(const item of items){this.children.push(item);if(this.tagName==='select')this.options.push(item);}}
  appendChild(item){this.append(item);}
  replaceChildren(...items){this.children=[...items];if(this.tagName==='select')this.options=[...items];}
  setAttribute(name,value){this.attributes[name]=String(value);}
  getAttribute(name){return this.attributes[name];}
  remove(index){this.options.splice(index,1);this.children.splice(index,1);}
  querySelector(){return null;}
  focus(){}
  showModal(){this.open=true;}
  close(){this.open=false;return this.emit('close');}
}

const text=node=>node.textContent||node.children.map(text).join('');

test('la fiche Domotique annule le brouillon et valide les réglages ensemble',async()=>{
  const originals=new Map();
  const replace=(name,value)=>{originals.set(name,Object.getOwnPropertyDescriptor(globalThis,name));Object.defineProperty(globalThis,name,{value,configurable:true,writable:true});};
  const elements=new Map(),requests=[];
  const element=id=>{if(!elements.has(id))elements.set(id,new Node(id==='home-device-room'?'select':id));return elements.get(id);};
  const document={getElementById:element,createElement:tag=>new Node(tag),hidden:false};
  const window={dispatchEvent(){},};window.window=window;
  const config={configured:true,verified:true,base_url:'http://ha.test:8123',room:'Bureau',storage:'test'};
  const catalog={entities:[
    {entity_id:'switch.imprimante',name:'Imprimante',ha_name:'Imprimante',area:'Bureau',ha_area:'Bureau',domain:'switch',allowed:true,confirmation_required:true},
    {entity_id:'switch.prise',name:'Prise',ha_name:'Prise',area:'Salon',ha_area:'Salon',domain:'switch',allowed:true,confirmation_required:false}],
    ha_rooms:['Bureau','Salon','Atelier']};
  replace('document',document);replace('window',window);
  replace('sessionStorage',{getItem(){return null;},setItem(){}});
  replace('crypto',{randomUUID:()=> 'home-session-000001'});
  replace('CustomEvent',class{constructor(type,options){this.type=type;this.detail=options?.detail;}});
  replace('fetch',async(path,options={})=>{
    requests.push({path,options});
    if(path==='/api/home/config')return Response.json(config);
    if(path==='/api/home/catalog')return Response.json(catalog);
    if(path==='/api/home/devices')return Response.json({settings:{
      alfred_name:'',alfred_area:'Atelier',allowed:true,confirmation_required:true,aliases:[],
    }});
    if(path==='/api/home/command'){
      const body=JSON.parse(options.body);
      if(body.text==='oui')return Response.json({reply:'Imprimante activée.'});
      return Response.json({status:'confirmation',reply:'Voulez-vous vraiment allumer Imprimante ?'});
    }
    throw new Error('Requête inattendue : '+path);
  });
  try{
    await import(new URL(`../alfred/static/home-panel.js?scenario=${Date.now()}`,import.meta.url));
    await settle();
    const table=element('home-catalog-list').children[0];
    const headers=table.children[0].children[0].children.map(text);
    assert.ok(headers.includes('Confirmation'));
    const rows=table.children[1].children;
    const prise=rows.find(row=>text(row.children[0]).includes('Prise'));
    const edit=prise.children.at(-1).children[0];
    const dialog=element('home-device-editor');
    const room=element('home-device-room');
    const confirmation=element('home-device-confirmation');
    await edit.emit('click');
    assert.ok(dialog.open);
    assert.deepEqual(room.options.map(option=>[option.value,option.textContent]),
      [['','Salon'],['Atelier','Atelier'],['Bureau','Bureau']]);
    assert.equal(element('home-device-room-icon').hidden,false);
    room.value='Atelier';
    await element('home-device-cancel').emit('click');
    assert.equal(dialog.open,false);
    assert.ok(!requests.some(x=>x.path==='/api/home/devices'));
    await edit.emit('click');
    assert.equal(room.value,'');
    room.value='Atelier';
    confirmation.checked=true;
    await element('home-device-editor-form').emit('submit');
    const saved=requests.filter(x=>x.path==='/api/home/devices');
    assert.equal(saved.length,1);
    assert.equal(saved[0].options.method,'PATCH');
    assert.deepEqual(JSON.parse(saved[0].options.body),{
      id:'switch.prise',settings:{alfred_area:'Atelier',confirmation_required:true},
    });
    assert.equal(dialog.open,false);
    assert.match(text(element('home-catalog-list')),/PriseAtelierswitchAutoriséActivée/);

    element('home-text').value='allume imprimante';
    await element('home-command-form').emit('submit');await settle();
    assert.equal(element('home-confirmation').hidden,false);
    assert.match(element('home-confirmation-text').textContent,/Voulez-vous vraiment/);
    await element('home-confirmation-yes').emit('click');await settle();
    const answers=requests.filter(x=>x.path==='/api/home/command').map(x=>JSON.parse(x.options.body));
    assert.equal(answers.at(-1).text,'oui');
    assert.equal(answers.at(-1).session_id,'home-session-000001');
  }finally{
    for(const [name,descriptor] of originals){if(descriptor)Object.defineProperty(globalThis,name,descriptor);else delete globalThis[name];}
  }
});
