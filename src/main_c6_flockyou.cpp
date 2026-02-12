/*
 * Standalone Flock-You entry point for XIAO ESP32-C6
 *
 * This file replaces main.cpp for the C6 single-mode build.
 * No selector UI, no other modes — just Flock-You.
 */

#include "modes.h"

void setup() {
    flockyou_setup();
}

void loop() {
    flockyou_loop();
}
