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

username = input("Username: ")

clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
clientSocket.connect((serverName, serverPort))

def keyboard_interrupt_handler(signal, frame):
    print("\r[SHUTDOWN] Connection to server has been closed.")
    clientSocket.close()
    exit(0)

def recv_handler():
    global clientSocket
    while True:
        try:
            # Receive Message From Server
            message = clientSocket.recv(1024).decode()
            if message == 'PROMPT_COMMANDS':
                reply = input("PROMPT_COMMANDS: ")
                clientSocket.send(reply.encode('utf-8'))
            else:
                print(message)
        except:
            # Close Connection When Error
            print("An error occured!")
            clientSocket.close()
            break

def send_handler():
    global clientSocket
    while True:
        message = '{}: {}'.format(username, input(''))
        clientSocket.send(message.encode())

def start():
    recv_thread = threading.Thread(target=recv_handler)
    recv_thread.daemon = True
    recv_thread.start()

    send_thread = threading.Thread(target=send_handler)
    send_thread.daemon = True
    send_thread.start()

    signal.signal(signal.SIGINT, keyboard_interrupt_handler)

    while True:
        time.sleep(0.1)

def login():
    pass
start()