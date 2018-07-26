int sensor=A0;

void setup() {
Serial.begin(9600);

}
void loop() 
{
   int c=analogRead(sensor);
  Serial.println(c);
  if(c>2)
  Serial.println("accident detected");
  
  delay(1000);
}
