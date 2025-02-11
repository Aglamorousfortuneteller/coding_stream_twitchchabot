#include <FastLED.h>

#define LED_PIN 6
#define NUM_LEDS 50
#define CHIPSET WS2812
#define COLOR_ORDER RGB

CRGB leds[NUM_LEDS];

bool rainbowActive=false;

void setup() {
    Serial.begin(115200);
    Serial.println("FastLED Serial Control Ready!");
    Serial.println("Commands:");
    Serial.println(" - <LED#> ON   (Turn on specific LED in white)");
    Serial.println(" - <LED#> OFF  (Turn off specific LED)");
    Serial.println(" - ALL ON      (Turn all LEDs white)");
    Serial.println(" - ALL OFF     (Turn all LEDs off)");
    Serial.println(" - <LED#> R    (Set specific LED to red)");
    Serial.println(" - <LED#> G    (Set specific LED to green)");
    Serial.println(" - <LED#> B    (Set specific LED to blue)");
    Serial.println(" - <LED#> <R> <G> <B> (Set specific LED to custom colour)");
    Serial.println(" - RAINBOW ON");
    Serial.println(" - RAINBOW OFF");
    
    FastLED.addLeds<CHIPSET, LED_PIN, COLOR_ORDER>(leds, NUM_LEDS);
    FastLED.clear();
    FastLED.show();
}

void loop() {
    checkSerialInput();
    if (rainbowActive){
      rainbowCycle();
    }


    FastLED.show();
}

void checkSerialInput() {
    if (Serial.available()) {
        String command = Serial.readStringUntil('\n');
        command.trim();

        if (command.equals("ALL ON")) {
            fill_solid(leds, NUM_LEDS, CRGB::White);
            Serial.println("All LEDs turned ON.");
        } else if (command.equals("ALL OFF")) {
            FastLED.clear();
            rainbowActive=false;
            Serial.println("All LEDs turned OFF.");  
        } 
        else if (command.equals("RAINBOW ON")) {
            rainbowActive=true;
            Serial.println("Rainbow effect started.");  
        } 
        else if (command.equals("RAINBOW OFF")) {
            rainbowActive=false;

            Serial.println("Rainbow effect stoped.");  
        } 
        
        else {
            processLEDCommand(command);
        }
    }
}

void processLEDCommand(String command) {
    int firstSpace = command.indexOf(' ');
    if (firstSpace == -1) {
        Serial.println("Invalid command format!");
        return;
    }

    String ledNumberStr = command.substring(0, firstSpace);
    ledNumberStr.trim();
    int ledNumber = ledNumberStr.toInt();

    if (ledNumber < 0 || ledNumber >= NUM_LEDS) {
        Serial.println("Invalid LED number!");
        return;
    }

    String action = command.substring(firstSpace + 1);
    action.trim();

    if (action.equals("ON")) {
        leds[ledNumber] = CRGB::White;
        Serial.print("LED ");
        Serial.print(ledNumber);
        Serial.println(" turned ON (White).");
    } else if (action.equals("OFF")) {
        leds[ledNumber] = CRGB::Black;
        Serial.print("LED ");
        Serial.print(ledNumber);
        Serial.println(" turned OFF.");
    } else if (action.equals("R")) {
        leds[ledNumber] = CRGB::Red;
        Serial.print("LED ");
        Serial.print(ledNumber);
        Serial.println(" set to Red.");
    } else if (action.equals("G")) {
        leds[ledNumber] = CRGB::Green;
        Serial.print("LED ");
        Serial.print(ledNumber);
        Serial.println(" set to Green.");
    } else if (action.equals("B")) {
        leds[ledNumber] = CRGB::Blue;
        Serial.print("LED ");
        Serial.print(ledNumber);
        Serial.println(" set to Blue.");
    } 
    else {
      int space1= action.indexOf(' ');
      int space2= action.indexOf(' ', space1+1);
      if (space1 ==-1 || space2 ==-1){
        Serial.println("Unknown command.");
        return;
    }
    int r=action.substring(0,space1).toInt();
    int g=action.substring(space1+1, space2).toInt();
    int b=action.substring(space2+1).toInt();

    if (r<0 || r>255 || g<0 || g>255 || b<0 ||b>255){
      Serial.println("Invalid RGB input");
      return;
    }
    leds[ledNumber]=CRGB(r,g,b);
    Serial.print("LED");
    Serial.print("ledNumber");
    Serial.print("set to RGB");
    Serial.print(r);
    Serial.print(", ");
    Serial.print(g);
    Serial.print(", ");
    Serial.print(b);
    Serial.print(".");
    }
FastLED.show();
}

void rainbowCycle() {
    static uint8_t hue = 0;
    fill_rainbow(leds, NUM_LEDS, hue, 10);
    hue += 5;
    FastLED.delay(5);
}
