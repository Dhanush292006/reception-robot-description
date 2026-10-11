/*
  Wi-Fi UDP motor receiver for an ESP32-WROOM-32 development board.

  UDP payload sent to ROBOT_UDP_PORT:
    CMD,sequence,front_left,front_right,rear_left,rear_right
  Wheel speeds are signed rad/s. Each motor needs its own H-bridge channel.
  Full mecanum control is impossible with only the pictured single L298N.
*/
#include <Arduino.h>
#include <WiFi.h>
#include <WiFiUdp.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>
#include "esp_arduino_version.h"

// Set these to the 2.4 GHz Wi-Fi network used by the ROS computer.
const char *WIFI_SSID = "YOUR_WIFI_NAME";
const char *WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";
static constexpr uint16_t ROBOT_UDP_PORT = 8888;

static constexpr uint32_t PWM_FREQUENCY_HZ = 18000;
static constexpr uint8_t PWM_RESOLUTION_BITS = 8;
static constexpr float MAX_WHEEL_RAD_S = 20.0f;
static constexpr uint32_t COMMAND_WATCHDOG_MS = 500;
static constexpr size_t PACKET_BUFFER_SIZE = 128;

// Example GPIO allocation. Change to match your four H-bridge channels.
// Per motor: IN1, IN2, EN(PWM). Remove each L298N ENA/ENB jumper for PWM.
struct MotorPins { uint8_t in1; uint8_t in2; uint8_t enable; bool invert; };
MotorPins motors[4] = {
  {16, 17, 18, false},  // front-left, driver 1 channel A
  {19, 21, 22, false},  // front-right, driver 1 channel B
  {23, 25, 26, false},  // rear-left, driver 2 channel A
  {27, 32, 33, false}   // rear-right, driver 2 channel B
};

#if ESP_ARDUINO_VERSION_MAJOR < 3
static constexpr uint8_t PWM_CHANNELS[4] = {0, 1, 2, 3};
#endif

WiFiUDP udp;
uint32_t lastValidCommandMs = 0;
uint32_t lastWiFiAttemptMs = 0;
bool udpStarted = false;

void writePwm(size_t motorIndex, uint8_t duty) {
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  ledcWrite(motors[motorIndex].enable, duty);
#else
  ledcWrite(PWM_CHANNELS[motorIndex], duty);
#endif
}

void stopAllMotors() {
  for (size_t i = 0; i < 4; ++i) {
    writePwm(i, 0);
    digitalWrite(motors[i].in1, LOW);
    digitalWrite(motors[i].in2, LOW);
  }
}

void setMotor(size_t i, float radPerSecond) {
  if (!isfinite(radPerSecond)) radPerSecond = 0.0f;
  radPerSecond = constrain(radPerSecond, -MAX_WHEEL_RAD_S, MAX_WHEEL_RAD_S);
  if (motors[i].invert) radPerSecond = -radPerSecond;
  if (fabsf(radPerSecond) < 0.02f) {
    writePwm(i, 0);
    digitalWrite(motors[i].in1, LOW);
    digitalWrite(motors[i].in2, LOW);
    return;
  }
  digitalWrite(motors[i].in1, radPerSecond > 0.0f ? HIGH : LOW);
  digitalWrite(motors[i].in2, radPerSecond > 0.0f ? LOW : HIGH);
  const uint8_t duty = static_cast<uint8_t>(fabsf(radPerSecond) * 255.0f / MAX_WHEEL_RAD_S);
  writePwm(i, duty);
}

bool parseCommand(char *packet, float speeds[4]) {
  if (strncmp(packet, "CMD,", 4) != 0) return false;
  char *cursor = packet + 4;
  char *end = nullptr;
  (void)strtoul(cursor, &end, 10);  // sequence number
  if (end == cursor || *end != ',') return false;
  cursor = end + 1;
  for (size_t i = 0; i < 4; ++i) {
    speeds[i] = strtof(cursor, &end);
    if (end == cursor || !isfinite(speeds[i])) return false;
    if (i < 3) {
      if (*end != ',') return false;
      cursor = end + 1;
    } else if (*end != '\0') {
      return false;
    }
  }
  return true;
}

void connectWiFi() {
  WiFi.mode(WIFI_STA);
  WiFi.setSleep(false);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.printf("Connecting to Wi-Fi: %s", WIFI_SSID);
  while (WiFi.status() != WL_CONNECTED) {
    delay(300);
    Serial.print('.');
  }
  Serial.println();
  Serial.print("Robot Wi-Fi IP: ");
  Serial.println(WiFi.localIP());
  udpStarted = udp.begin(ROBOT_UDP_PORT);
  Serial.printf("UDP command port %u: %s\n", ROBOT_UDP_PORT, udpStarted ? "ready" : "failed");
  lastWiFiAttemptMs = millis();
}

void setup() {
  Serial.begin(115200);  // diagnostics only; motor commands use Wi-Fi UDP
  for (size_t i = 0; i < 4; ++i) {
    pinMode(motors[i].in1, OUTPUT);
    pinMode(motors[i].in2, OUTPUT);
    pinMode(motors[i].enable, OUTPUT);
#if ESP_ARDUINO_VERSION_MAJOR >= 3
    ledcAttach(motors[i].enable, PWM_FREQUENCY_HZ, PWM_RESOLUTION_BITS);
#else
    ledcSetup(PWM_CHANNELS[i], PWM_FREQUENCY_HZ, PWM_RESOLUTION_BITS);
    ledcAttachPin(motors[i].enable, PWM_CHANNELS[i]);
#endif
  }
  stopAllMotors();
  lastValidCommandMs = millis();
  connectWiFi();
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    stopAllMotors();
    if (udpStarted) udp.stop();
    udpStarted = false;
    if (millis() - lastWiFiAttemptMs > 2000) connectWiFi();
    if (millis() - lastValidCommandMs > COMMAND_WATCHDOG_MS) stopAllMotors();
    delay(10);
    return;
  }
  if (!udpStarted) udpStarted = udp.begin(ROBOT_UDP_PORT);

  const int packetSize = udp.parsePacket();
  if (packetSize > 0) {
    char packet[PACKET_BUFFER_SIZE];
    const int count = udp.read(packet, sizeof(packet) - 1);
    while (udp.available()) udp.read();
    if (count > 0) {
      packet[count] = '\0';
      float speeds[4];
      if (parseCommand(packet, speeds)) {
        for (size_t i = 0; i < 4; ++i) setMotor(i, speeds[i]);
        lastValidCommandMs = millis();
      }
    }
  }
  if (millis() - lastValidCommandMs > COMMAND_WATCHDOG_MS) stopAllMotors();
}
