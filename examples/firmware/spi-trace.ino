// Bit-banged SPI mode 0, captured from actual GPIO writes.
// CLK D13, MOSI D11, CS D10. Transmit A5 3C.
void setup(){pinMode(13,OUTPUT);pinMode(11,OUTPUT);pinMode(10,OUTPUT);digitalWrite(10,HIGH);}
void sendByte(byte value){for(int bit=7;bit>=0;bit--){digitalWrite(11,(value>>bit)&1);delayMicroseconds(5);digitalWrite(13,HIGH);delayMicroseconds(5);digitalWrite(13,LOW);}}
void loop(){digitalWrite(10,LOW);sendByte(0xa5);sendByte(0x3c);digitalWrite(10,HIGH);delay(2);}
