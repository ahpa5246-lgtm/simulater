#include <Adafruit_BMP085.h>
Adafruit_BMP085 bmp;
void setup(){Serial.begin(9600);if(!bmp.begin(BMP085_ULTRAHIGHRES))Serial.println("BMP180 missing");}
void loop(){Serial.print("T: ");Serial.println(bmp.readTemperature(),1);Serial.print("P: ");Serial.println(bmp.readPressure());delay(10);}
