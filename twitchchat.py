import socket
from dotenv import load_dotenv
import os
import serial
import re

load_dotenv()

HOST = 'irc.chat.twitch.tv'
PORT = 6667
TOKEN = os.getenv("TWITCH_OAUTH_TOKEN")
CHANNEL = "aglamorousfortuneteller"

ARDUINO_PORT = "COM6"
BAUD_RATE = 115200 
arduino = serial.Serial(ARDUINO_PORT, BAUD_RATE, timeout=1) 

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
        arduino.write(f"{command}\n".encode('utf-8')) 

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
                message = message.strip().lower()
                if "ping" in message:
                    sendMessage(s, f"@{user}, PONG")
                elif "💖" in message:
                    sendMessage(s, f"@{user} Hi! 💖💖💖")
                elif "rainbow on" in message: 
                    sendMessage(s, f"@{user} Turning the Rainbow ON")
                    controlArduino("RAINBOW ON") 
                elif "rainbow off" in message:
                    sendMessage(s, f"@{user} Turning the Rainbow off!") 
                    controlArduino("RAINBOW OFF") 
                elif "all leds on" in message: 
                    sendMessage(s, f"@{user} Turning all the LED on!")
                    controlArduino("ALL ON") 
                elif "all leds off" in message:
                    sendMessage(s, f"@{user} Turning all the LED off!") 
                    controlArduino("ALL OFF") 
                
                
                match_color = re.match(r"led(\d+) (r|g|b|red|green|blue)$", message)
                if match_color:
                    led_num = match_color.group(1)
                    color = match_color.group(2)

                    color_map = {
                        "r": "R", "g": "G", "b": "B",
                        "red": "R", "green": "G", "blue": "B"
                    }
                    mapped_color = color_map[color]

                    sendMessage(s, f"@{user} Setting LED {led_num} to {mapped_color}")
                    controlArduino(f" {led_num} {mapped_color}")

            
                match_rgb = re.match(r"led(\d+) (\d{1,3}) (\d{1,3}) (\d{1,3})$", message)
                if match_rgb:
                    led_num = match_rgb.group(1)
                    r, g, b = int(match_rgb.group(2)), int(match_rgb.group(3)), int(match_rgb.group(4))

                    if 0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255:
                        sendMessage(s, f"@{user} Setting LED {led_num} to RGB({r}, {g}, {b})")
                        controlArduino(f" {led_num} {r} {g} {b}")
                    else:
                        sendMessage(s, f"@{user} Invalid RGB values! Use 0-255.")





if __name__ == "__main__":
    s = openSocket()
    sendMessage(s, "Hello, world!")
    listenAndRespond(s)