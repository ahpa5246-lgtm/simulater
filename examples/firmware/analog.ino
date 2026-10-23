// Sensor output -> A0; power -> 5V / GND
void setup() {
  Serial.begin(9600);
  pinMode(13, OUTPUT);
}

void loop() {
  int raw = analogRead(A0);
  float volts = raw * (5.0 / 1024.0);
  digitalWrite(13, raw > 100);

  Serial.print("ADC: ");
  Serial.print(raw);
  Serial.print("  Voltage: ");
  Serial.println(volts, 3);
  delay(10);
}
