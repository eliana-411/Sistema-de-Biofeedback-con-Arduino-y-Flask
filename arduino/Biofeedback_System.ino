#include <MySignals.h>
#include "Wire.h"
#include "SPI.h"

const int SEND_INTERVAL = 100;  // 100ms (10 Hz)
unsigned long lastSendTime = 0;
unsigned long sessionStartTime = 0;

// Pin del ECG en MySignals
const int ECG_PIN = A1;

void setup() {
  Serial.begin(115200);
  MySignals.begin();
  delay(2000);
  
  Serial.println("SYSTEM:READY");
  sessionStartTime = millis();
}

void loop() {
  unsigned long currentTime = millis();
  
  if (currentTime - lastSendTime >= SEND_INTERVAL) {
    
    // Leer ECG directamente del pin (más confiable)
    int ecgRaw = analogRead(ECG_PIN);
    
    // Convertir a voltaje (Arduino: 0-1023 = 0-5V)
    float ecgVoltage = (ecgRaw * 5.0) / 1023.0;
    
    // Leer Temperatura
    float temperature = MySignals.getTemperature();
    
    // Timestamp relativo
    unsigned long relativeTime = currentTime - sessionStartTime;
    
    // Formato: DATA:timestamp,ecg_raw,ecg_voltage,temperature
    Serial.print("DATA:");
    Serial.print(relativeTime);
    Serial.print(",");
    Serial.print(ecgRaw);
    Serial.print(",");
    Serial.print(ecgVoltage, 4);
    Serial.print(",");
    Serial.println(temperature, 2);
    
    lastSendTime = currentTime;
  }
  
  delay(1);
}
