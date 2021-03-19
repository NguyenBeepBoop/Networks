# Written by Nguyen Hoang z5257125
# Python --Version 3.7.3
import sys
from socket import *
import threading
import time
import datetime
import signal
import json

UPDATE_INTERVAL = 1
IP = 'localhost'
timeout = False
t_lock=threading.Condition()
block_time = 10

CURRENT_USERS = []

BLOCKED_CLIENTS = {}

# Get the server port and attempts allowed for login
try:
    PORT = int(sys.argv[1])
    ATTEMPTS = int(sys.argv[2])
    if PORT < 1024:
        print("Port number must be greater than 1024")
        sys.exit()
    if ATTEMPTS > 5 or ATTEMPTS < 1:
        print("Attempts must be between 1 and 5")
except:
    print("Usage: Python3 server.py <PORT> <ATTEMPTS>")
    sys.exit(1)

serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
serverSocket.bind((IP, PORT))

##################################################
def client_exit(client):
    global t_lock
    with t_lock:
        for user in CURRENT_USERS:
            if user == client:
                CURRENT_USERS.remove(user)
        client.close()
        t_lock.notify()

def keyboard_interrupt_handler(signal, frame):
    print("\r[SHUTDOWN] Server has been shutdown")
    exit(0)

def populate_logins():
    user_logins = {}
    with open("credentials.txt", 'r') as file:
        for line in file:
            (username, password) = line.split()
            user_logins[username] = password
    return user_logins

def broadcast(message):
    for client in CURRENT_USERS:
        client.send(message)

def block():
    pass
def prompt_commands(client, username):
    while True:
        try:
            client.send('PROMPT_COMMANDS'.encode('utf-8'))
            message = client.recv(1024)
            broadcast(message)
        except:
            print(f'{username} has disconnected')
            broadcast('{username} has left the chat!'.encode('utf-8'))
            client_exit()

def prompt_login(client):
    global CURRENT_USERS
    global logins
    global t_lock
    with t_lock:
        while True:
            username = client.recv(1024).decode('utf-8')
            if username in logins:
                client.send('VALID_USERNAME'.encode('utf-8'))
                break
            else:
                client.send('INVALID_USERNAME'.encode('utf-8'))
        login_attempts = 1
        while login_attempts < ATTEMPTS:
            password = client.recv(1024).decode()
            if logins[username] != password:  
                client.send('INCORRECT_PASSWORD'.encode('utf-8'))
                login_attempts += 1
            elif logins[username] == password:
                print(f'{username} has sucessfully logged in.')
                client.send('SUCCESS'.encode('utf-8'))
                CURRENT_USERS.append(client)
                t_lock.notify()
                return (True, username)
        t_lock.notify()
        return (False, username)

def client_handler(client):
    global t_lock
    global CURRENT_USERS
    global serverSocket
    try:
        login_status = prompt_login(client)
        if login_status[0]:
            prompt_commands(client, login_status[1])
    except:
        client_exit(client)

def recv_handler():
    global serverSocket
    while True:
        client, addr = serverSocket.accept()
        print(f'[CONNECTION] connected with address {str(addr)}')
        client_thread = threading.Thread(target=client_handler, args=(client,))
        client_thread.start()

def send_handler():
    global t_lock
    global CURRENT_USERS
    global serverSocket
    while True:
        # get lock
        with t_lock:
         
            t_lock.notify()

logins = populate_logins()

print("[STARTING] server is starting...")

serverSocket.listen(1)
print("[READY] Server is ready for service")
print("Running on http://127.0.0.1:" + str(PORT) + "/")
recv_thread = threading.Thread(name="RecvHandler", target=recv_handler)
recv_thread.daemon = True
recv_thread.start()

send_thread = threading.Thread(name="SendHandler", target=send_handler)
send_thread.daemon = True
send_thread.start()

signal.signal(signal.SIGINT, keyboard_interrupt_handler)

while True:
    time.sleep(0.1)