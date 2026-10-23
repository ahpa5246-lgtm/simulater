#include <Wire.h>
// PICSimLab DS1621 register adapter: address 0x48, SDA A4 / SCL A5.
void setup(){Serial.begin(9600);Wire.begin();}
void loop(){Wire.beginTransmission(0x48);Wire.write(0xaa);byte error=Wire.endTransmission();if(error){Serial.println("NACK");}else{Wire.requestFrom(0x48,2);if(Wire.available()==2){int16_t raw=Wire.read()<<8;raw|=Wire.read();Serial.println(raw/256.0,1);}}delay(10);}
