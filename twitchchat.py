import socket
from dotenv import load_dotenv
import os
import serial

load_dotenv()

HOST = 'irc.chat.twitch.tv'
PORT = 6667
TOKEN = os.getenv("TWITCH_OAUTH_TOKEN")
CHANNEL = "aglamorousfortuneteller"

ARDUINO_PORT = "COM8"
BAUD_RATE = 9600 
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
                elif "led1 on" in message: 
                    sendMessage(s, f"@{user} Turning the LED №1 on!")
                    controlArduino("LED1_ON") 
                elif "led1 off" in message:
                    sendMessage(s, f"@{user} Turning the LED №1 off!") 
                    controlArduino("LED1_OFF") 
                
                elif "led2 on" in message: 
                    sendMessage(s, f"@{user} Turning the LED №2 on!")
                    controlArduino("LED2_ON") 
                elif "led2 off" in message:
                    sendMessage(s, f"@{user} Turning the LED №2 off!") 
                    controlArduino("LED2_OFF") 

                elif "led3 on" in message: 
                    sendMessage(s, f"@{user} Turning the LED №3 on!")
                    controlArduino("LED3_ON") 
                elif "led3 off" in message:
                    sendMessage(s, f"@{user} Turning the LED №3 off!") 
                    controlArduino("LED3_OFF") 

if __name__ == "__main__":
    s = openSocket()
    sendMessage(s, "Hello, world!")
    listenAndRespond(s)