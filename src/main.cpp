#include "Arduino.h"
#include "config.h"



struct TTEST {
  char id[3];
  bool test_bool;
  uint8_t ipadress[4];
  uint8_t volume;
  uint16_t freq;
  bool test_bool2;
  uint16_t count;
  uint32_t u32test;
  float flfoo;
  int testint;
  char yess[8];
  uint16_t leet_time;
} struct_data = {
  "01",
  true,
  { 10, 9, 5, 241 },
  22,
  1234,
  false,
  6699,
  568902,
  1337.337,
  -55,
  "oh yeah",
  1337
};

struct RCONFIG {
  uint8_t volume;
  uint16_t freq;
  uint16_t pause;
  uint16_t count;
} ringer_config = {
  240,
  30,
  250,
  22
};


void send_struct(){
  char b[sizeof(struct_data)];
  memcpy(b, &struct_data, sizeof(struct_data));
  //Serial.write(sizeof(struct_data));
  //delay(10);
  for (int i=0; i<(sizeof(b)+1); i++){
    Serial.write(b[i]);
  }
}


void setup() {
  Serial.begin(SERIAL_BAUD);
}

uint8_t serial_command;

void loop() {
  if (Serial.available()) {
    serial_command = Serial.read();
    switch (serial_command) {

      // on
      case 51:
        send_struct();
        break;

    }
  }
  delay(1);
}
