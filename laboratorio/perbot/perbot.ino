// PER-bot v2 — entrega automática do estímulo + LED de sincronização
// Hardware: Arduino Uno/Nano, micro servo (SG90) no pino 9, LED no pino 7 (com resistor 220 ohm)
// Protocolo serial (115200 baud), um comando por linha, enviado pelo per_control.py:
//   P<n>   -> apresenta o estímulo por n ms (ex.: P2000) e recolhe
//   A<ang> -> calibra ângulo de apresentação (ex.: A95)
//   R<ang> -> calibra ângulo de repouso (ex.: R40)
//   ?      -> responde a configuração atual
// O LED acende exatamente enquanto a mecha toca a mosca: no vídeo, ele marca o instante do estímulo.
#include <Servo.h>
Servo arm;
const int SERVO_PIN = 9, LED_PIN = 7;
int angRest = 40, angPresent = 95;
const int SETTLE_MS = 250;  // tempo para o servo chegar

void setup() {
  Serial.begin(115200);
  pinMode(LED_PIN, OUTPUT);
  arm.attach(SERVO_PIN);
  arm.write(angRest);
  Serial.println("PERBOT_READY");
}

void present(unsigned long ms) {
  arm.write(angPresent);
  delay(SETTLE_MS);
  digitalWrite(LED_PIN, HIGH);
  unsigned long t0 = millis();
  Serial.print("ON "); Serial.println(t0);
  delay(ms);
  digitalWrite(LED_PIN, LOW);
  Serial.print("OFF "); Serial.println(millis());
  arm.write(angRest);
  delay(SETTLE_MS);
  Serial.println("DONE");
}

void loop() {
  if (!Serial.available()) return;
  String cmd = Serial.readStringUntil('\n');
  cmd.trim();
  if (cmd.length() == 0) return;
  char c = cmd.charAt(0);
  long v = cmd.substring(1).toInt();
  if (c == 'P') present(v > 0 ? v : 2000);
  else if (c == 'A') { angPresent = v; arm.write(angPresent); Serial.println("OK"); }
  else if (c == 'R') { angRest = v; arm.write(angRest); Serial.println("OK"); }
  else if (c == '?') { Serial.print("rest="); Serial.print(angRest); Serial.print(" present="); Serial.println(angPresent); }
  else Serial.println("ERR");
}
