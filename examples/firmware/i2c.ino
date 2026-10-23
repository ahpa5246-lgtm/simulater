#include <Wire.h>

// LM75 subset: SDA -> A4, SCL -> A5
void setup() {
  Serial.begin(9600);
  Wire.begin();
}

void loop() {
  Wire.beginTransmission(0x48);
  Wire.write(0); // temperature register
  Wire.endTransmission();
  Wire.requestFrom(0x48, 2);

  if (Wire.available() == 2) {
    int16_t raw = (Wire.read() << 8);
    raw |= Wire.read();
    Serial.print("Temperature: ");
    Serial.print(raw / 256.0, 1);
    Serial.println(" C");
  }
  delay(10);
}
