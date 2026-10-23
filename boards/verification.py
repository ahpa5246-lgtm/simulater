"""Reproducible internal reference tests; results require actual CPU execution."""
from datetime import datetime, timezone
from pathlib import Path
from .service import run_board

EXAMPLES=('analog','i2c','blink','ultrasonic','digital','servo','buzzer','pwm','ds1621','spi-trace','bmp180')
ROOT=Path(__file__).resolve().parents[1]/'examples/firmware'

def example_hex():return {name:(ROOT/f'{name}.hex').read_text() for name in EXAMPLES}
def example_sketches():return {name:(ROOT/f'{name}.ino').read_text() for name in EXAMPLES}

def verify_models():
    firmware=example_hex();cases=[]
    def check(name,sketch,config,extract,expected,tolerance=0,unit=''):
        result=run_board({'board':'arduino-uno','hex':firmware[sketch],'durationMs':100,**config})
        measured=extract(result)
        numeric=isinstance(measured,(int,float)) and isinstance(expected,(int,float))
        error=abs(measured-expected) if numeric else 0 if measured==expected else None
        passed=error is not None and error<=tolerance
        cases.append({'name':name,'expected':expected,'measured':measured,'error':error,'tolerance':tolerance,'unit':unit,'passed':passed,'firmwareSha256':result['evidence']['firmwareSha256'],'cycles':result['cycles'],'clockHz':result['evidence']['clockHz'],'inputs':config,'serial':result['serial'][:300],'tracePreview':result['logic'][:16],'traceTruncated':result['evidence']['traceTruncated']})
    for distance in (20,100,200):
        config={'devices':[{'model':'hcsr04','distanceCm':distance,'triggerPin':3,'echoPin':2}]}
        check(f'HC-SR04 {distance} cm · captured ECHO','ultrasonic',config,lambda r:r['instruments']['D2']['highUs'],distance*58,.25,'µs')
        check(f'HC-SR04 {distance} cm · firmware pulseIn','ultrasonic',config,lambda r:int(r['serial'].splitlines()[0]),distance*58,4,'µs')
    check('Disconnected ECHO · firmware timeout','ultrasonic',{'devices':[]},lambda r:int(r['serial'].splitlines()[0]),0,0,'µs')
    for pressed in (False,True):
        check('Button '+('pressed' if pressed else 'released'),'digital',{'devices':[{'model':'button','pin':2,'value':pressed}]},lambda r:int(r['serial'].splitlines()[0]),0 if pressed else 1,0,'logic')
    check('NTC10k at 25 °C · divider midpoint','analog',{'sensors':[{'model':'ntc10k','pin':0,'value':25}]},lambda r:int(r['serial'].split('ADC: ')[1].split()[0]),512,1,'ADC counts')
    check('Timer1 servo-style pulse width','servo',{},lambda r:r['instruments']['D9']['highUs'],1500,1,'µs')
    check('Timer1 servo-style repetition','servo',{},lambda r:r['instruments']['D9']['frequencyHz'],50,.05,'Hz')
    check('Buzzer tone frequency','buzzer',{},lambda r:r['instruments']['D9']['frequencyHz'],1000,2,'Hz')
    check('I²C absent address returns NACK','i2c',{'i2cPresent':False},lambda r:any(e.get('ack') is False for e in r['bus']),True,0,'bus')
    skipped=[]
    try:
        run_board({'board':'arduino-uno','hex':firmware['ds1621'],'durationMs':100,'i2cModel':'ds1621','i2cTemperature':25})
    except (ValueError,RuntimeError) as error:
        skipped.append('Native PICSimLab checks unavailable: '+str(error))
    else:
        for temperature in (-10.5,25.5,100):
            check(f'DS1621 native · {temperature} °C','ds1621',{'i2cModel':'ds1621','i2cTemperature':temperature},lambda r:float(r['serial'].splitlines()[0]),temperature,0,'°C')
        for temperature,pressure in ((10,900),(25,1013.25),(40,1050)):
            config={'i2cModel':'bmp180','i2cTemperature':temperature,'i2cPressureHpa':pressure,'durationMs':150}
            check(f'BMP180 Adafruit driver · {temperature} °C','bmp180',config,lambda r:float(r['serial'].split('T: ')[1].split()[0]),temperature,.2,'°C')
            check(f'BMP180 Adafruit driver · {pressure} hPa','bmp180',config,lambda r:int(r['serial'].split('P: ')[1].split()[0]),pressure*100,200,'Pa')
    return {'scope':'Internal firmware/reference verification, not physical hardware validation. Ideal and subset model assumptions still apply.','skipped':skipped,'generatedAt':datetime.now(timezone.utc).isoformat(),'passed':sum(c['passed'] for c in cases),'failed':sum(not c['passed'] for c in cases),'cases':cases,'reference':'HC-SR04 58 µs/cm; ATmega328P Timer1 16 MHz / 8; generic 10k/B3950 divider; 10-bit ADC; absent I²C address NACK.'}
