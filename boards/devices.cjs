// Behavioral digital-device models. No acoustic scene or mechanical physics is implied.
function attachDevices(cpu,ports,config){
 if(!Array.isArray(config)||config.length>8)throw Error('At most eight digital devices are supported.');
 const used=new Set(),inputs=[],devices=[],events=[];
 const portFor=pin=>({port:pin<8?ports.D:ports.B,index:pin<8?pin:pin-8});
 const claim=pin=>{if(!Number.isInteger(pin)||pin<2||pin>13||used.has(pin))throw Error('Invalid or conflicting digital device pin (D2–D13).');used.add(pin);};
 const log=(type,data)=>{if(events.length<500)events.push({cycle:cpu.cycles,ms:cpu.cycles/16000,type,...data});};
 const drive=(pin,value)=>{const p=portFor(pin);p.port.setPin(p.index,value);};
 for(const item of config){
  if(!item||typeof item!=='object')throw Error('Invalid digital device.');
  if(item.model==='hcsr04'){
   const trig=item.triggerPin??3,echo=item.echoPin??2;claim(trig);claim(echo);inputs.push(echo);
   const distance=item.distanceCm===undefined?100:item.distanceCm;
   if(distance!==null&&(typeof distance!=='number'||!Number.isFinite(distance)||distance<2||distance>400))throw Error('HC-SR04 distance must be 2–400 cm, or null for no echo.');
   let highAt=null,busy=false;const p=portFor(trig);drive(echo,false);
   p.port.addListener((value,old)=>{const mask=1<<p.index;if(!((value^old)&mask))return;if(value&mask){highAt=cpu.cycles;return;}if(highAt===null)return;const width=cpu.cycles-highAt;highAt=null;log('trigger',{pin:'D'+trig,widthUs:width/16});if(width<160||busy||distance===null)return;
    busy=true;const pulse=Math.round(distance*58*16);cpu.addClockEvent(()=>{drive(echo,true);log('echo-start',{pin:'D'+echo});cpu.addClockEvent(()=>{drive(echo,false);busy=false;log('echo-end',{pin:'D'+echo,widthUs:pulse/16});},pulse);},3200);
   });devices.push({model:item.model,triggerPin:trig,echoPin:echo,distanceCm:distance,assumption:'≥10 µs trigger; 200 µs response delay; echo width 58 µs/cm; no scene/acoustic model'});
  }else if(['button','pir','reed-switch','ir-obstacle'].includes(item.model)){
   claim(item.pin);inputs.push(item.pin);if(typeof item.value!=='boolean')throw Error('Digital device value must be true or false.');const activeLow=item.model!=='pir';drive(item.pin,activeLow?!item.value:item.value);devices.push({...item,activeLow,assumption:'Ideal digital signal; no bounce, optics, magnetic or motion physics'});
  }else throw Error('Unsupported digital sensor model.');
 }
 return {devices,events,diagnostics(){return inputs.filter(pin=>{const p=portFor(pin);return cpu.data[p.port.portConfig.DDR]&(1<<p.index);}).map(pin=>`Device input D${pin} is configured as an MCU output; check wiring/pinMode.`);}};
}
module.exports={attachDevices};
