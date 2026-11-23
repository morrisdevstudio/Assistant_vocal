import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {readFile} from 'node:fs/promises';

class Element {
  constructor() { this.children=[];this.value='';this.listeners=new Map();this.classList={toggle(){}}; }
  addEventListener(name,fn) { this.listeners.set(name,fn); }
  async emit(name) { await this.listeners.get(name)?.({preventDefault(){}}); }
  replaceChildren(...items) { this.children=[...items]; }
  append(...items) { this.children.push(...items); }
  add(item) { this.append(item); }
  get childElementCount() { return this.children.length; }
}

test('sources : liens sûrs, titres affichés comme texte et effacement du tour précédent',async()=>{
  const list=new Element();
  const context=vm.createContext({window:{},URL,document:{getElementById:()=>list,
    createElement:()=>new Element(),createTextNode:text=>({textContent:text})}});
  vm.runInContext(await readFile(new URL('../alfred/static/internet-sources.js',import.meta.url),'utf8'),context);
  context.window.renderInternetSources([
    {url:'javascript:alert(1)',title:'invalide'},
    {url:'https://example.org/',title:'<script>injection</script>',date:'2026-11-16'},
    {url:'https://user:pass@example.org/',title:'invalide'}]);
  assert.equal(list.children.length,1);
  const link=list.children[0].children[0];
  assert.equal(link.textContent,'<script>injection</script>');
  assert.equal(link.rel,'noopener noreferrer');
  assert.equal(list.hidden,false);
  context.window.renderInternetSources([]);
  assert.equal(list.hidden,true);
  assert.equal(list.children.length,0);
});

test('réglages Internet : choix de commune, clé effacée et quota rafraîchi',async()=>{
  const elements=new Map(),requests=[],listeners=new Map();
  const el=id=>{if(!elements.has(id))elements.set(id,new Element());return elements.get(id);};
  let used=0;
  const config=()=>({configured:true,credit_limit:1000,credits_used:used,month:'2026-11',storage:'test',location:null});
  const context=vm.createContext({document:{getElementById:el},
    window:{location:{hash:'#settings'},addEventListener:(name,fn)=>listeners.set(name,fn)},
    Option:class {constructor(text,value){this.textContent=text;this.value=value;}},
    fetch:async(path,options={})=>{
      requests.push({path,...options});
      return {ok:true,json:async()=>path.startsWith('/api/internet/locations')
        ?{results:[{id:42,name:'Paris',admin1:'Île-de-France',country:'France'}]}:config()};
    }});
  const script=await readFile(new URL('../alfred/static/internet-panel.js',import.meta.url),'utf8');
  await vm.runInContext('(async()=>{'+script+'})()',context);
  el('internet-city').value='Paris, France';await el('internet-location-form').emit('submit');
  assert.equal(el('internet-locations').children[1].value,42);
  el('internet-locations').value='42';el('internet-key').value='test-only-secret';el('internet-limit').value='50';
  await el('internet-config-form').emit('submit');
  const saved=requests.find(r=>r.path==='/api/internet/config'&&r.method==='POST');
  assert.equal(JSON.parse(saved.body).location_id,42);
  assert.equal(JSON.parse(saved.body).credit_limit,50);
  assert.equal(el('internet-key').value,'');
  used=12;await listeners.get('hashchange')();
  assert.match(el('internet-usage').textContent,/12 \/ 1000/);
});
