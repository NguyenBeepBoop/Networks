#Python 3
#Usage: python3 client.py localhost 5000
#coding: utf-8
from socket import *
import threading
import sys
import time
import signal
import json

#Server would be running on the same host as Client
if len(sys.argv) == 3:
    serverName = sys.argv[1]
    serverPort = int(sys.argv[2])
else:
    print("usage: python3 client.py <serverAddress> <serverPort>")
    sys.exit(1)

clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
clientSocket.connect((serverName, serverPort))

serverMessage = ""
message = ""

def keyboard_interrupt_handler(signal, frame):
    print("\r[SHUTDOWN] Connection to server has been closed.")
    clientSocket.close()
    exit(0)

def recv_handler():
    global clientSocket
    global serverMessage
    global message
    while True:
        try:
            # Receive Message From Server
            serverMessage = clientSocket.recv(1024).decode('utf-8')
            print("> ", end="")    
            if serverMessage == 'PROMPT_COMMANDS':
                print("Enter one of thefollowing commands (MSG, DLT, EDT, RDM, ATU, OUT):", end=" ")
            else:
                print(message)
        except:
            # Close Connection When Error
            clientSocket.close()
            break

def send_handler():
    global clientSocket
    global serverMessage
    global message
    while True:
        time.sleep(0.1)
        try:
            if serverMessage == 'PROMPT_COMMANDS':
                message = input("")
            clientSocket.send(message.encode('utf-8'))

        except:
            clientSocket.close()
            break

def start():
    print("Welcome to Toom!")
    recv_thread = threading.Thread(target=recv_handler)
    recv_thread.daemon = False
    recv_thread.start()

    send_thread = threading.Thread(target=send_handler)
    send_thread.daemon = False
    send_thread.start()

    while True:
        time.sleep(0.1)

def login():
    global clientSocket
    while True:
        clientSocket.send(input("Username: ").encode('utf-8'))
        usernameStatus = clientSocket.recv(1024).decode('utf-8')
        if usernameStatus == 'INVALID_USERNAME':
            print("Please enter a valid username.")
        elif usernameStatus == 'VALID_USERNAME':
            break
    clientSocket.send(input("Password: ").encode('utf-8'))
    while True:
        try:
            login_result = clientSocket.recv(1024).decode('utf-8')
            if login_result == 'SUCCESS':
                start()
                break
            elif login_result == 'INCORRECT_PASSWORD':
                print("Invalid Password. Please try again")
                clientSocket.send(input("Password: ").encode('utf-8'))
        except:
            clientSocket.close()
            break

signal.signal(signal.SIGINT, keyboard_interrupt_handler)
login()