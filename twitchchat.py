import socket
import time
from dotenv import load_dotenv
import os
import serial
import re
import random

load_dotenv()

HOST = 'irc.chat.twitch.tv'
PORT = 6667
TOKEN = os.getenv("TWITCH_OAUTH_TOKEN")
CHANNEL = "aglamorousfortuneteller"
BOT_NICK="greenwitchbi"
ARDUINO_PORT = "COM8"
BAUD_RATE = 115200 
arduino = serial.Serial(ARDUINO_PORT, BAUD_RATE, timeout=1) 

active_users={}
total_leds=50

flat_led_map={
    1: [0,9,10],
    2:[1,8],
    3:[2,7],
    4:[3,6],
    5:[4,5],
    6:[33,42],
    7:[44,45],
    8:[34,41],
    9:[46],
    10:[35,40],
    11:[47],
    12:[39,36],
    13:[47],
    14:[37,38],
    15:[49],
    "staircase": list(range(11,32)) +[43],
}





def openSocket():
    s = socket.socket()
    s.connect((HOST, PORT))
    s.send(f"PASS {TOKEN}\r\n".encode('utf-8'))
    s.send(f"NICK {CHANNEL}\r\n".encode('utf-8'))
    s.send(f"JOIN #{CHANNEL}\r\n".encode('utf-8'))
    return s

def sendMessage(s, message):
    s.send(f"PRIVMSG #{CHANNEL} :{message}\r\n".encode('utf-8'))
    print(f"Sent: {message}")

def getUser(line):
    if "PRIVMSG" in line:
        return line.split("!", 1)[0][1:]
    return None

def getMessage(line):
    if "PRIVMSG" in line:
        return line.split(" :", 1)[1]
    return None

def controlArduino(command): 
    if arduino.is_open: 
        arduino.flush()
        command += "\n"
        arduino.write(command.encode('utf-8'))
        print(f"Arduino Command Sent: {command}")
        time.sleep(0.5)



def assignLedToUser(user):
    if user == BOT_NICK:
        return

    if user not in active_users:
        available_flats = list(set(flat_led_map.keys()) - set(active_users.values()))
        if available_flats:
            assigned_flat=random.choice(available_flats)
            active_users[user]=assigned_flat
            sendMessage(s,f"@{user} You got an appartment {assigned_flat}! 🏠")

            for led in flat_led_map[assigned_flat]:
                text_to_arduino=(f"{led} 255 255 255")
                time.sleep(0.05)
                controlArduino(text_to_arduino)
                time.sleep(0.05)
                controlArduino(text_to_arduino)
                time.sleep(0.05)
                controlArduino(text_to_arduino)
                time.sleep(0.05)
                controlArduino(text_to_arduino)
        else:
            sendMessage(s,f"@{user} No more free appartments available!")


def listenAndRespond(s):
    buffer = ""
    while True:
        buffer += s.recv(2048).decode('utf-8')
        lines = buffer.split("\r\n")
        buffer = lines.pop()
        
        for line in lines:
            print(f"Received: {line}")
            
            if "PING :tmi.twitch.tv" in line:
                s.send("PONG :tmi.twitch.tv\r\n".encode('utf-8'))
                print("Sent: PONG to server")
                continue
            user = getUser(line)
            message = getMessage(line)
            if user and message:
                message = message.strip().casefold()

                assignLedToUser(user)

                if "ping" in message:
                    sendMessage(s, f"@{user}, PONG")
                elif "💖" in message:
                    sendMessage(s, f"@{user} Hi! 💖💖💖")

                elif "rainbow on" in message:
                    if "enter" in message:
                        a=[]
                    else:
                        sendMessage(s, f"@{user} Turning the Rainbow ON")
                        controlArduino("RAINBOW ON")
                        time.sleep(0.05)

                elif "rainbow off" in message:
                    if "enter" in message:
                        a=[]
                    else:
                        sendMessage(s, f"@{user} Turning the Rainbow off!")

                        controlArduino("RAINBOW OFF")
                        time.sleep(0.05)

                elif "all on" in message:
                    if "enter" in message:
                        a=[]
                    else:
                        sendMessage(s, f"@{user} Turning all the LED on!")
                        controlArduino("ALL ON")
                        time.sleep(0.05)

                elif "all off" in message:
                    if "enter" in message:
                        a=[]
                    else:
                        sendMessage(s, f"@{user} Turning all the LED off!")
                        controlArduino("ALL OFF")
                        time.sleep(0.05)
                
                match_flat_color = re.match(r"flat(\w+)\s+(r|g|b|w|off|red|green|blue|white)$", message)
                if match_flat_color:
                    flat = int(match_flat_color.group(1))
                    color = match_flat_color.group(3).lower()
                    try:
                        flat=int(flat)
                    except ValueError:
                        flat=flat

                    if flat in flat_led_map:
                        leds_to_change=flat_led_map[flat]
                        color_map = {
                            "r": "R", "g": "G", "b": "B",
                            "red": "R", "green": "G", "blue": "B",
                            "w": "W", "white": "W", "off": "OFF"
                        }
                        if color in color_map:
                            mapped_color=color_map[color]
                            for led in leds_to_change:
                                if mapped_color == "OFF":
                                    controlArduino(f"{led} OFF")
                                    time.sleep(0.05)
                                    controlArduino(f"{led} OFF")
                                    time.sleep(0.05)
                                elif mapped_color == "W":
                                    controlArduino(f"{led} 255 255 255")
                                    time.sleep(0.05)
                                    controlArduino(f"{led} 255 255 255")
                                    time.sleep(0.05)
                                else:
                                    controlArduino(f"{led} {mapped_color}")
                                    time.sleep(0.05)
                                    controlArduino(f"{led} {mapped_color}")
                                    time.sleep(0.05)
                            sendMessage(s, f"@{user} set flat {flat} LEDs to {mapped_color}")
                        else:
                            sendMessage(s, f"@{user} Unknown color for flat.")
                    else:
                        sendMessage(s, f"@{user} Unknown flat number.")

                match_flat_rgb=re.match(r"flat(\w+)\s+(\d{1,3})\s+(\d{1,3})\s+(\d{1,3})$", message)
                if match_flat_rgb:
                    flat=match_flat_rgb.group(1)
                    try:
                        flat=int(flat)
                    except ValueError:
                        flat=flat

                    r = int(match_flat_rgb.group()[1:])
                    g = int(match_flat_rgb.group()[1:])
                    b = int(match_flat_rgb.group()[1:])

                    if flat in flat_led_map:
                        if all(0<= v<=255 for v in (r,g,b)):
                            for led in flat_led_map[flat]:
                                controlArduino(f"{led} {r} {g} {b}")
                                time.sleep(0.05)
                                controlArduino(f"{led} {r} {g} {b}")
                                time.sleep(0.05)
                            sendMessage(s, f"@{user} Flat {flat} set to RGB({r},{g},{b})")
                        else:
                            sendMessage(s, f"@{user} invalid RGB values!")
                

if __name__ == "__main__":
    s = openSocket()
    sendMessage(s, "Join the house!")
    controlArduino("ALL OFF")
    listenAndRespond(s)