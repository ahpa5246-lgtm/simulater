import unittest
from boards.service import compile_sketch,run_board

ULTRASONIC='''
void setup(){Serial.begin(9600);pinMode(3,OUTPUT);pinMode(2,INPUT);}
void loop(){digitalWrite(3,LOW);delayMicroseconds(2);digitalWrite(3,HIGH);delayMicroseconds(12);digitalWrite(3,LOW);noInterrupts();unsigned long us=pulseIn(2,HIGH,30000);interrupts();Serial.println(us);delay(65);}
'''
BUTTON='''
void setup(){Serial.begin(9600);pinMode(2,INPUT_PULLUP);pinMode(13,OUTPUT);}
void loop(){int reading=digitalRead(2);digitalWrite(13,!reading);Serial.println(reading);delay(10);}
'''
PWM="""
void setup(){pinMode(9,OUTPUT);TCCR1A=0;TCCR1B=0;TCNT1=0;ICR1=39999;OCR1A=3000;TCCR1A=_BV(COM1A1)|_BV(WGM11);TCCR1B=_BV(WGM13)|_BV(WGM12)|_BV(CS11);}
void loop(){}
"""
NTC='''void setup(){Serial.begin(9600);}void loop(){Serial.println(analogRead(A0));delay(10);}'''

class SensorProtocols(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.echo=compile_sketch(ULTRASONIC)['hex'];cls.button=compile_sketch(BUTTON)['hex'];cls.pwm=compile_sketch(PWM)['hex'];cls.ntc=compile_sketch(NTC)['hex']
    def run_firmware(self,firmware,**config):return run_board({'board':'arduino-uno','hex':firmware,'durationMs':100,**config})
    def test_ultrasonic_edges_are_measured_by_real_pulsein(self):
        for distance in (20,100,200):
            result=self.run_firmware(self.echo,devices=[{'model':'hcsr04','distanceCm':distance,'triggerPin':3,'echoPin':2}])
            measured=int(result['serial'].splitlines()[0]);self.assertAlmostEqual(measured,distance*58,delta=5)
            self.assertAlmostEqual(result['instruments']['D2']['highUs'],distance*58,delta=.2)
    def test_disconnected_echo_produces_timeout_instead_of_fake_distance(self):
        result=self.run_firmware(self.echo,devices=[])
        self.assertEqual(int(result['serial'].splitlines()[0]),0)
    def test_button_pullup_and_led_are_connected_through_firmware(self):
        for pressed in (False,True):
            result=self.run_firmware(self.button,devices=[{'model':'button','pin':2,'value':pressed}])
            self.assertEqual(result['serial'].splitlines()[0],'0' if pressed else '1')
            self.assertEqual(result['pins']['D13'],pressed)
    def test_gpio_instrument_recovers_servo_style_pulses(self):
        result=self.run_firmware(self.pwm)
        self.assertAlmostEqual(result['instruments']['D9']['highUs'],1500,delta=10)
        self.assertAlmostEqual(result['instruments']['D9']['frequencyHz'],50,delta=.1)
        self.assertIn('$timescale 1ns',result['vcd'])
    def test_ntc_divider_uses_beta_curve(self):
        at25=self.run_firmware(self.ntc,sensors=[{'model':'ntc10k','value':25,'pin':0}])
        at50=self.run_firmware(self.ntc,sensors=[{'model':'ntc10k','value':50,'pin':0}])
        self.assertAlmostEqual(int(at25['serial'].splitlines()[0]),512,delta=1)
        self.assertLess(int(at50['serial'].splitlines()[0]),int(at25['serial'].splitlines()[0]))
    def test_two_devices_cannot_drive_the_same_input(self):
        with self.assertRaisesRegex(ValueError,'pin'):self.run_firmware(self.button,devices=[{'model':'button','pin':2,'value':True},{'model':'pir','pin':2,'value':True}])

if __name__=='__main__':unittest.main()
