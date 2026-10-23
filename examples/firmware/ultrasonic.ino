// Original Mina reference sketch; see docs/instrument-validation.md for assumptions.

void setup(){Serial.begin(9600);pinMode(3,OUTPUT);pinMode(2,INPUT);}
void loop(){digitalWrite(3,LOW);delayMicroseconds(2);digitalWrite(3,HIGH);delayMicroseconds(12);digitalWrite(3,LOW);noInterrupts();unsigned long us=pulseIn(2,HIGH,30000);interrupts();Serial.println(us);delay(65);}
