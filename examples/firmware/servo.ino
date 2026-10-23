// Original Mina reference sketch; see docs/instrument-validation.md for assumptions.

void setup(){pinMode(9,OUTPUT);TCCR1A=0;TCCR1B=0;TCNT1=0;ICR1=39999;OCR1A=3000;TCCR1A=_BV(COM1A1)|_BV(WGM11);TCCR1B=_BV(WGM13)|_BV(WGM12)|_BV(CS11);}
void loop(){}
