# Written by Nguyen Hoang z5257125
# Python --Version 3.9.1
from socket import *
import threading
import sys
import time
import signal
import json

# Server would be running on the same host as Client
if len(sys.argv) == 3:
    serverName = sys.argv[1]
    serverPort = int(sys.argv[2])
else:
    print("usage: python3 client.py <serverAddress> <serverPort>")
    sys.exit(1)

clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
clientSocket.connect((serverName, serverPort))

p2pSocket = socket(AF_INET, SOCK_STREAM)
p2pSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
IP = clientSocket.getsockname()[0]
PORT = clientSocket.getsockname()[1]
print(IP, PORT)
p2pSocket.bind((IP, PORT))

serverMessage = ""
message = ""
command = ""
running = True
def keyboard_interrupt_handler(signal, frame):
    print("\r[SHUTDOWN] Connection to server has been closed.")
    clientSocket.close()
    sys.exit(1)

def client_exit(clientSocket):
    global running
    clientSocket.close()
    running=False
    sys.exit(1)

def p2p_recv_handler():
    pass

def recv_handler():
    global clientSocket
    global serverMessage
    global message
    global command
    global running
    while running:
        try:
            # Receive Message From Server
            serverMessage = clientSocket.recv(1024).decode('utf-8')
            data=json.loads(serverMessage)
            command=data["command"]
            print("> ", end="")
            if command == 'PROMPT_COMMANDS':
                print("Enter one of the following commands (MSG, DLT, EDT, RDM, ATU, OUT, UPD):", end=" ")
            elif command == 'INVALID_COMMAND':
                print("Error. Invalid command!")
            elif command == 'PRINT':
                print(data['message'])
            elif command == 'ATU':
                activeUsers=data['message']
                for user in activeUsers:
                    print(user)
            elif command == 'RDM':
                messages=data['message']
                for msg in messages:
                    print(msg)
            elif command == 'OUT':
                print(data['message'])
                client_exit(clientSocket)
            else:
                print(command)
                # TODO other server commands 
        except:
            # Close Connection When Error
            client_exit(clientSocket)
            break

def send_handler():
    global clientSocket
    global serverMessage
    global message
    global command
    global running
    while running:
        time.sleep(0.1)
        try:
            if command == 'PROMPT_COMMANDS':
                message = input("")
                clientSocket.send(message.encode('utf-8'))
        except:
            clientSocket.close()
            break

def start():
    global running
    print("Welcome to Toom!")
    recv_thread = threading.Thread(target=recv_handler)
    recv_thread.daemon = False
    recv_thread.start()

    send_thread = threading.Thread(target=send_handler)
    send_thread.daemon = False
    send_thread.start()

    p2p_thread = threading.Thread(target=p2p_recv_handler)
    p2p_thread.daemon = True
    p2p_thread.start()

    while running:
        time.sleep(0.1)

def login():
    global clientSocket
    global running
    while True:
        clientSocket.send(input("> Username: ").encode('utf-8'))
        usernameStatus = clientSocket.recv(1024).decode('utf-8')
        if usernameStatus == 'INVALID_USERNAME':
            print("> Please enter a valid username.")
        elif usernameStatus == 'VALID_USERNAME':
            break
    clientSocket.send(input("> Password: ").encode('utf-8'))
    while True:
        try:
            login_result = clientSocket.recv(1024).decode('utf-8')
            if login_result == 'SUCCESS':
                start()
                break
            elif login_result == 'ALREADY_LOGGED':
                print("> This account is already logged in.")
                clientSocket.close()
                sys.exit(1)
            elif login_result == 'BLOCKED':
                print("> Your account is blocked due to multiple login failures. Please try again later")
                clientSocket.close()
                sys.exit(1)
            elif login_result == 'BLOCK_LOGIN':
                print("> Invalid Password. Your account has been blocked. Please try again later")
                clientSocket.close()
                sys.exit(1)
            elif login_result == 'INCORRECT_PASSWORD':
                print("> Invalid Password. Please try again")
                clientSocket.send(input("> Password: ").encode('utf-8'))
        except:
            clientSocket.close()
            break

signal.signal(signal.SIGINT, keyboard_interrupt_handler)
login()