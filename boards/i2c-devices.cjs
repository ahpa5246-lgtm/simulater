// Behavioral byte-level models; see docs/practical-simulation.md for datasheets and limits.
const CLOCK=16000000;
function finite(value,min,max,label){if(typeof value!=='number'||!Number.isFinite(value)||value<min||value>max)throw Error(`${label} must be ${min}–${max}.`);return value;}
function createI2CBus(cpu,configs){
 if(!Array.isArray(configs)||configs.length>16)throw Error('At most 16 I2C devices are supported.');
 const devices=new Map();let selected=null,writeMode=false;
 for(const c of configs){
  if(!c||typeof c!=='object')throw Error('Invalid I2C device.');
  const defaults={lm75:0x48,ds1621:0x48,bmp180:0x77,ads1115:0x48,bh1750:0x23,pcf8574:0x20};
  if(!(c.model in defaults))throw Error('Unsupported I2C model: '+c.model);
  if('connected' in c&&typeof c.connected!=='boolean')throw Error('Connected must be boolean.');
  const address=c.address??defaults[c.model];
  const allowed={lm75:[0x48,0x4f],ds1621:[0x48,0x4f],bmp180:[0x77,0x77],ads1115:[0x48,0x4b],pcf8574:[0x20,0x27]};
  if(!Number.isInteger(address)||(c.model==='bh1750'?![0x23,0x5c].includes(address):address<allowed[c.model][0]||address>allowed[c.model][1]))throw Error('Invalid address for '+c.model);
  if(devices.has(address))throw Error('I2C address conflict at 0x'+address.toString(16));
  let readIndex=0,writeIndex=0,pointer=0,state={model:c.model,address};
  let device;
  if(c.model==='lm75'){
   const temperature=finite(c.temperature??25,-55,125,'LM75 temperature');let config=0;const thresholds=[0x4b00,0x5000];
   device={begin(){readIndex=writeIndex=0;},write(v){if(writeIndex++===0)pointer=v&3;else if(pointer===1)config=v&0x1f;else if(pointer>1){const shift=(writeIndex%2===0)?8:0;thresholds[pointer-2]=(thresholds[pointer-2]&(~(255<<shift)))|(v<<shift);}},read(){if(pointer===1)return config;const raw=pointer===0?(Math.round(temperature*2)<<7)&65535:thresholds[pointer-2];return (raw>>(readIndex++%2===0?8:0))&255;},snapshot:()=>({...state,temperature,config,pointer})};
  }else if(c.model==='pcf8574'){
   const inputs=finite(c.inputs??255,0,255,'PCF8574 inputs');if(!Number.isInteger(inputs))throw Error('PCF8574 inputs must be an integer byte.');let latch=255;
   device={begin(){},write(v){latch=v;},read:()=>latch&inputs,snapshot:()=>({...state,latch,inputs,pins:latch&inputs,limitations:'Quasi-bidirectional logic; no IRQ/current model'})};
  }else if(c.model==='bh1750'){
   const lux=finite(c.lux??100,0,100000,'BH1750 lux');let powered=false,mode=null,mt=69,ready=Infinity,result=0;
   const period=()=>((mode&3)===3?16:120)*mt/69*16000;
   function update(){if(cpu.cycles<ready)return;result=Math.min(65535,Math.round(lux*1.2*mt/69*((mode&3)===1?2:1)));if(mode>=0x20){powered=false;ready=Infinity;}else ready=cpu.cycles+period();}
   device={begin(){readIndex=0;},write(v){update();if(v===0){powered=false;ready=Infinity;}else if(v===1)powered=true;else if(v===7&&powered)result=0;else if((v&0xe0)===0x40)mt=(mt&31)|((v&7)<<5);else if((v&0xe0)===0x60)mt=(mt&224)|(v&31);else if([0x10,0x11,0x13,0x20,0x21,0x23].includes(v)){if(mt<31||mt>254)throw Error('BH1750 MTreg outside supported 31–254 range.');powered=true;mode=v;ready=cpu.cycles+period();}},read(){update();return(result>>(readIndex++%2===0?8:0))&255;},snapshot(){update();return {...state,lux,powered,mode,mt,raw:result,readyAtCycle:Number.isFinite(ready)?ready:null,limitations:'Nominal timing and ideal lux conversion; no spectrum/noise model'};}};
  }else if(c.model==='ads1115'){
   const volts=c.voltages??[0,0,0,0];if(!Array.isArray(volts)||volts.length!==4)throw Error('ADS1115 requires four input voltages.');volts.forEach(v=>finite(v,0,5,'ADS1115 input voltage'));
   let config=0x8583,activeConfig=0x8583,conversion=0,ready=Infinity,high=0,lowThreshold=0x8000,highThreshold=0x7fff;
   function finish(){if(cpu.cycles<ready)return;const mux=(activeConfig>>12)&7,pga=(activeConfig>>9)&7;const pairs=[[0,1],[0,3],[1,3],[2,3]];const v=mux>=4?volts[mux-4]:volts[pairs[mux][0]]-volts[pairs[mux][1]];const fs=[6.144,4.096,2.048,1.024,.512,.256,.256,.256][pga];conversion=Math.max(-32768,Math.min(32767,Math.round(v/fs*32768)))&65535;ready=(config&0x100)?Infinity:cpu.cycles+CLOCK/[8,16,32,64,128,250,475,860][(config>>5)&7];activeConfig=config;}
   function value(){finish();return [conversion,(config&0x7fff)|(Number.isFinite(ready)?0:0x8000),lowThreshold,highThreshold][pointer];}
   device={begin(){readIndex=writeIndex=0;},write(v){finish();if(writeIndex++===0){pointer=v&3;return;}if(writeIndex===2){high=v;return;}const word=(high<<8)|v;if(pointer===1){const wasBusy=Number.isFinite(ready);config=word;if(!wasBusy&&(!(word&0x100)||(word&0x8000))){activeConfig=word;ready=cpu.cycles+CLOCK/[8,16,32,64,128,250,475,860][(word>>5)&7];}}else if(pointer===2)lowThreshold=word;else if(pointer===3)highThreshold=word;writeIndex=1;},read(){return(value()>>(readIndex++%2===0?8:0))&255;},snapshot(){finish();return {...state,voltages:volts,config,conversion,busy:Number.isFinite(ready),limitations:'Ideal ADC and nominal data rate; comparator/ALERT, noise and source impedance omitted'};}};
  }else{
   if(c.connected===false){devices.set(address,{present:false,begin(){},read:()=>255,write(){},snapshot:()=>({...state,connected:false})});continue;}
   const temp=finite(c.temperature??25,-55,c.model==='bmp180'?85:125,'Temperature');let native;try{native=require('../.tools/picsimlab-ds1621.node');}catch{throw Error('Build the PICSimLab adapter first: python scripts/build-picsimlab.py');}
   const handle=c.model==='bmp180'?native.createBMP(temp,finite(c.pressureHpa??1013.25,300,1100,'Pressure')):native.create(temp);
   device={begin(){readIndex=writeIndex=0;},write(v){native.write(handle,v,writeIndex++);},read:()=>native.read(handle,readIndex++),snapshot:()=>({...state,temperature:temp,adapter:'PICSimLab native',limitations:'Native register subset; no physical conversion timing'})};
  }
  devices.set(address,{...device,present:c.connected!==false});
 }
 return {connect(address,write){selected=devices.get(address);if(!selected?.present){selected=null;return false;}writeMode=write;selected.begin(write);return true;},write(value){if(!selected||!writeMode)return false;selected.write(value);return true;},read(){return selected&&!writeMode?selected.read():255;},stop(){selected=null;},snapshots:()=>[...devices.values()].map(d=>({...d.snapshot(),connected:d.present}))};
}
module.exports={createI2CBus};
