// Shared terminal metadata for palette, schematic and import validation.
import parts from './analog-parts.json' with {type:'json'};
export {parts};
const byId=new Map(parts.map(p=>[p.id,p]));
const defaults={R:'resistor',C:'capacitor',L:'inductor',D:'silicon-diode',V:'v-dc',I:'i-dc'};
export function partFor(c){const p=byId.get(c.part===undefined?defaults[c.type]:c.part);if(!p||p.type!==c.type)throw Error('Invalid component profile.');return p;}
export function waveform(c){return c.wave??partFor(c).wave??'dc';}
export function pinsFor(c){return partFor(c).pins;}
export function makePart(partId,id,x,y){
 const p=byId.get(partId),c={id,type:p.type,part:p.id,value:p.value,x,y,rotation:0};
 for(const pin of p.pins)c[pin.key]=`n_${id}_${pin.key}`;
 if(p.wave){c.wave=p.wave;c.frequency=1000;}
 if(p.id==='potentiometer')c.ratio=.5;
 return c;
}
export function glyph(c,element){
 const p=partFor(c),g=element('g');let d;
 if(c.type==='R')d='M-60 0H-30 M-30 -10H30V10H-30Z M30 0H60';
 else if(c.type==='C')d='M-60 0H-8 M-8 -23V23 M8 -23V23 M8 0H60';
 else if(c.type==='L')d='M-60 0H-32 C-32 -26 -16 -26 -16 0 C-16 -26 0 -26 0 0 C0 -26 16 -26 16 0 C16 -26 32 -26 32 0 H60';
 else if(c.type==='D')d='M-60 0H-22 M-22 -20L18 0 -22 20Z M18 -22V22 M18 0H60';
 else if(c.type==='V'||c.type==='I'){
  d='M-60 0H-27 M27 0H60 M-27 0A27 27 0 1 0 27 0A27 27 0 1 0 -27 0 ';
  d+=c.type==='I'?'M-15 0H15 M7 -8L15 0 7 8':waveform(c)==='sine'?'M-17 0C-12 -22 -5 -22 0 0S12 22 17 0':'M-8 -8H8 M0 -16V0 M-8 12H8';
 }else if(c.type==='Q')d='M-60 0H-10 M-10 -25V25 M-10 -12L40 -35V-50 M-10 12L40 35V50 '+(p.id==='pnp'?'M10 15L0 17 4 27':'M23 33L34 31 30 21');
 else if(c.type==='M'||c.type==='J'){
  d='M-60 0H-16 M-16 -27V27 M-7 -25V25 M-7 -20H40V-50 M-7 20H40V50';
  if(c.type==='M')d+=' M0 60V35H12V0H-7 M4 -7L-7 0 4 7';
 }else if(p.id==='opamp'||p.id==='comparator'){
  d='M-60 -20H-30 M-60 20H-30 M-30 -40L35 0 -30 40Z M35 0H60 M0 -60V-23 M0 60V23';
  g.append(element('text',{x:-25,y:-15,'font-size':12},'+'),element('text',{x:-25,y:24,'font-size':12},'−'));
 }else if(p.id==='potentiometer')d='M-60 0H-30 M-30 -10H30V10H-30Z M30 0H60 M0 60V14 M-7 23L0 14 7 23';
 else{
  d=c.type==='X'?'M-30 -35H10Q40 -35 40 0Q40 35 10 35H-30Z':'M0 -34L32 0 0 34 -32 0Z';
  for(const pin of p.pins)d+=Math.abs(pin.x)>=60?` M${pin.x} ${pin.y}H${pin.x<0?-30:40}`:` M${pin.x} ${pin.y}V${pin.y<0?-35:35}`;
  g.append(element('text',{x:0,y:4,'font-size':p.id.length>6?7:10,'text-anchor':'middle'},c.type==='X'?p.id.toUpperCase():c.type));
 }
 g.append(element('path',{d,class:'part-symbol'}));return g;
}

export function validateShape(p){
 if(!p||p.version!==1||!Array.isArray(p.components)||p.components.length>150||!Array.isArray(p.wires)||p.wires.length>500||typeof p.name!=='string'||p.name.length>120)throw Error('Invalid project format.');
 const ids=new Map();
 for(const c of p.components){
  const profile=partFor(c);
  if(typeof c.id!=='string'||!new RegExp(`^${c.type}[A-Za-z0-9_]{1,30}$`).test(c.id)||ids.has(c.id.toLowerCase())||typeof c.value!=='number'||!Number.isFinite(c.value)||!profile.pins.every(({key})=>typeof c[key]==='string'&&/^(?:[A-Za-z_][A-Za-z0-9_]{0,31}|0)$/.test(c[key]))||!['x','y'].every(k=>typeof c[k]==='number'&&Number.isFinite(c[k])&&Math.abs(c[k])<10000)||![0,90,180,270].includes(c.rotation||0))throw Error('Invalid component in project.');
  if((c.wave!==undefined&&!['dc','sine','pulse'].includes(c.wave))||(c.frequency!==undefined&&(typeof c.frequency!=='number'||!Number.isFinite(c.frequency)||c.frequency<1||c.frequency>1e7)))throw Error('Invalid source waveform or frequency.');
  if(c.ratio!==undefined&&(typeof c.ratio!=='number'||!Number.isFinite(c.ratio)||c.ratio<0||c.ratio>1))throw Error('Invalid potentiometer ratio.');
  ids.set(c.id.toLowerCase(),c);
 }
 for(const w of p.wires)for(const key of ['a','b']){
  if(!w||typeof w[key]!=='string')throw Error('Invalid wire endpoint.');
  const [id,pin,...extra]=w[key].split(':'),c=ids.get(id.toLowerCase());
  if(extra.length||!c||c.id!==id||!pinsFor(c).some(p=>p.key===pin))throw Error('Invalid wire endpoint.');
 }
 if(p.analysis&&(!Number.isFinite(p.analysis.stop)||!Number.isFinite(p.analysis.step)||p.analysis.stop<=0||p.analysis.step<=0))throw Error('Invalid analysis settings.');
}
