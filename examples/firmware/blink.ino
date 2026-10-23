void setup() {
  pinMode(13, OUTPUT);
  Serial.begin(9600);
  Serial.println("GPIO timing test");
}

void loop() {
  digitalWrite(13, HIGH);
  delay(10);
  digitalWrite(13, LOW);
  delay(10);
}
