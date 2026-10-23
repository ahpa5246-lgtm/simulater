// Original Mina reference sketch; see docs/instrument-validation.md for assumptions.

void setup(){Serial.begin(9600);pinMode(2,INPUT_PULLUP);pinMode(13,OUTPUT);}
void loop(){int reading=digitalRead(2);digitalWrite(13,!reading);Serial.println(reading);delay(10);}
