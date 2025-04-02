import socket
import ssl
import time
import os
import serial
import re
import random
from dotenv import load_dotenv

load_dotenv()

HOST = 'irc.chat.twitch.tv'
PORT = 443
TOKEN = os.getenv("TWITCH_OAUTH_TOKEN")
CHANNEL = "aglamorousfortuneteller"
BOT_NICK = "greenwitchbi"
ARDUINO_PORT = "COM8"
BAUD_RATE = 115200 
arduino = serial.Serial(ARDUINO_PORT, BAUD_RATE, timeout=1)

active_users = {}
total_leds = 50

flat_led_map = {
    1: [0, 9, 10],
    2: [1, 8],
    3: [2, 7],
    4: [3, 6],
    5: [4, 5],
    6: [33, 42],
    7: [44, 45],
    8: [34, 41],
    9: [46],
    10: [35, 40],
    11: [47],
    12: [39, 36],
    13: [47],
    14: [37, 38],
    15: [49],
    "staircase": list(range(11, 32)) + [43],
}

def openSocket():
    print("🔌 Connecting to Twitch IRC over SSL...")
    raw_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    context = ssl.create_default_context()
    wrapped_socket = context.wrap_socket(raw_socket, server_hostname=HOST)
    wrapped_socket.connect((HOST, PORT))
    wrapped_socket.send(f"PASS {TOKEN}\r\n".encode('utf-8'))
    wrapped_socket.send(f"NICK {BOT_NICK}\r\n".encode('utf-8'))
    wrapped_socket.send("CAP REQ :twitch.tv/membership\r\n".encode('utf-8'))
    wrapped_socket.send("CAP REQ :twitch.tv/commands\r\n".encode('utf-8'))
    wrapped_socket.send("CAP REQ :twitch.tv/tags\r\n".encode('utf-8'))
    wrapped_socket.send(f"JOIN #{CHANNEL}\r\n".encode('utf-8'))
    print("✅ Connected and joined channel.")
    return wrapped_socket

def sendMessage(s, message):
    s.send(f"PRIVMSG #{CHANNEL} :{message}\r\n".encode('utf-8'))
    print(f"{BOT_NICK}: {message}")

def parseIRCMessage(line):
    if line.startswith("@"):
        parts = line.split(" ", 1)
        if len(parts) > 1:
            line = parts[1]
        else:
            return None, None
    if not line.startswith(":"):
        return None, None
    prefix, rest = line.split(" ", 1)
    user = prefix[1:].split("!", 1)[0]
    if " :" in rest:
        msg = rest.split(" :", 1)[1].strip()
    else:
        msg = ""
    return user, msg

def controlArduino(command):
    if arduino.is_open:
        arduino.flush()
        command += "\n"
        arduino.write(command.encode('utf-8'))
        print(f"Arduino Command Sent: {command}")
        time.sleep(1)

def assignLedToUser(user):
    if user == BOT_NICK or "tmi.twitch.tv" in user:
        return
    if user not in active_users:
        available_flats = list(set(flat_led_map.keys()) - set(active_users.values()))
        if "staircase" in available_flats:
            available_flats.remove("staircase")
        if available_flats:
            assigned_flat = random.choice(available_flats)
            active_users[user] = assigned_flat
            sendMessage(s, f"@{user} You got an appartment {assigned_flat}! 🏠")
            for led in flat_led_map[assigned_flat]:
                text = f"{led} 255 255 255"
                for _ in range(4):
                    controlArduino(text)
                    time.sleep(0.1)
        else:
            sendMessage(s, f"@{user} No more free appartments available!")



def listenAndRespond(s):
    buffer = ""
    while True:
        try:
            buffer += s.recv(2048).decode('utf-8')
        except socket.timeout:
            continue
        lines = buffer.split("\r\n")
        buffer = lines.pop()
        for line in lines:
            if line.startswith("PING"):
                s.send("PONG :tmi.twitch.tv\r\n".encode('utf-8'))
                print("Sent: PONG to server")
                continue
            user, message = parseIRCMessage(line)
            if user and message:
                print(f"{user}: {message}")
                if user not in active_users:
                    assignLedToUser(user)
                message_clean = message.strip().casefold()
                if "ping" in message_clean:
                    sendMessage(s, f"@{user}, PONG")
                elif "💖" in message_clean:
                    sendMessage(s, f"@{user} Hi! 💖💖💖")
                elif "rainbow on" in message_clean:
                    sendMessage(s, f"@{user} Turning the Rainbow ON")
                    controlArduino("RAINBOW ON")
                elif "rainbow off" in message_clean:
                    sendMessage(s, f"@{user} Turning the Rainbow off!")
                    controlArduino("RAINBOW OFF")
                elif "all on" in message_clean:
                    sendMessage(s, f"@{user} Turning all the LED on!")
                    controlArduino("ALL ON")
                elif "all off" in message_clean:
                    sendMessage(s, f"@{user} Turning all the LED off!")
                    controlArduino("ALL OFF")
                match_flat_color = re.match(r"flat(\w+)\s+(r|g|b|w|off|red|green|blue|white)$", message_clean)
                if match_flat_color:
                    flat = int(match_flat_color.group(1))
                    color = match_flat_color.group(2)
                    if flat in flat_led_map:
                        leds = flat_led_map[flat]
                        color_map = {
                            "r": "R", "g": "G", "b": "B",
                            "red": "R", "green": "G", "blue": "B",
                            "w": "W", "white": "W", "off": "OFF"
                        }
                        if color in color_map:
                            mapped_color = color_map[color]
                            for led in leds:
                                if mapped_color == "OFF":
                                    controlArduino(f"{led} OFF")
                                elif mapped_color == "W":
                                    controlArduino(f"{led} 255 255 255")
                                else:
                                    controlArduino(f"{led} {mapped_color}")
                            sendMessage(s, f"@{user} set flat {flat} LEDs to {mapped_color}")
                match_rgb = re.match(r"flat(\w+)\s+(\d{1,3})\s+(\d{1,3})\s+(\d{1,3})", message_clean)
                if match_rgb:
                    flat = int(match_rgb.group(1))
                    r, g, b = map(int, match_rgb.groups()[1:])
                    if flat in flat_led_map and all(0 <= v <= 255 for v in (r, g, b)):
                        for led in flat_led_map[flat]:
                            controlArduino(f"{led} {r} {g} {b}")
                        sendMessage(s, f"@{user} Flat {flat} set to RGB({r},{g},{b})")

if __name__ == "__main__":
    s = openSocket()
    sendMessage(s, "Join the house!")
    controlArduino("ALL OFF")
    listenAndRespond(s)