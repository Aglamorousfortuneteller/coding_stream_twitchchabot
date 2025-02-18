import socket
import time
from dotenv import load_dotenv
import os
import serial
import re
import random
import requests
import threading



load_dotenv()

HOST = 'irc.chat.twitch.tv'
PORT = 6667
TOKEN = os.getenv("TWITCH_OAUTH_TOKEN")
CHANNEL = "aglamorousfortuneteller"
BOT_NICK="greenwitchbi"
ARDUINO_PORT = "COM9"
BAUD_RATE = 115200 
arduino = serial.Serial(ARDUINO_PORT, BAUD_RATE, timeout=1) 

active_users={}
total_leds=50

def get_chatters():
    url=f"https://tmi.twitch.tv/group/user/{CHANNEL}/chatters"
    headers={
        "CLient-ID": TWITCH_CLIENT_ID,
        "Authorization": f"Bearer {TOKEN}"
    }

    try:
        responce = requests.get(url,headers=headers)
        if responce.status_code == 200:
            data=responce.json()
            chatters=data.get("chatters", {}).get("viewers", [])
            return chatters
        else:
            print(f"Error fetching chatters: {responce.status_code}")
            return []
    except Exception as e:
        print(f"Exception while fetching chatters: {e}")
        return []
    


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
        available_leds = list(set(range(1, total_leds + 1)) - set(active_users.values()))
        if available_leds:
            assigned_led=random.choice(available_leds)
            active_users[user]=assigned_led
            sendMessage(s,f"@{user} You got LED{assigned_led}! 💡")
            text_to_arduino=(f"{assigned_led} 255 255 255")
            controlArduino(text_to_arduino) 
        else:
            sendMessage(s,f"@{user} No more free LEDs available!")

def update_chatters():
    while True:
        chatters=get_chatters()
        if chatters:
            print(f"Active chatters: {chatters}")

            for user in chatters:
                assignLedToUser(user)

        time.sleep(120)


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

                elif "rainbow off" in message:
                    if "enter" in message:
                        a=[]
                    else:
                        sendMessage(s, f"@{user} Turning the Rainbow off!") 
                        controlArduino("RAINBOW OFF") 
                elif "all on" in message:
                    if "enter" in message:
                        a=[]
                    else:
                        sendMessage(s, f"@{user} Turning all the LED on!")
                        controlArduino("ALL ON") 
                elif "all off" in message:
                    if "enter" in message:
                        a=[]
                    else:
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
                    controlArduino(f"{led_num} {mapped_color}")

            
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
    controlArduino("ALL OFF")
    threading.Thread(target=update_chatters, daemon=True).start()
    listenAndRespond(s)