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
message = ""
CURRENT_USERS = []

USERNAMES = []

BLOCKED_CLIENTS = {}

MESSAGES = []

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

######################################################
def client_exit(client, username):
    """ close the connection to the client and remove the client from current users """
    global CURRENT_USERS
    global USERNAMES
    global t_lock
    with t_lock:
        CURRENT_USERS.remove(client)
        USERNAMES.remove(username)
        client.close()
        t_lock.notify()

def keyboard_interrupt_handler(signal, frame):
    """ print a shutdown message if server is closed with CTRL+C """
    print("\r[SHUTDOWN] Server has been shutdown")
    exit(0)

def populate_logins():
    """ populate login data from credentials.txt to logins """ 
    global BLOCKED_CLIENTS
    user_logins = {}
    with open("credentials.txt", 'r') as file:
        for line in file:
            (username, password) = line.split()
            user_logins[username] = password
            BLOCKED_CLIENTS[username] = False
    return user_logins

def broadcast(message):
    global CURRENT_USERS
    """ function to broadcast message to all users """
    for client in CURRENT_USERS:
        client.send(message.encode())

def send_message(client, username):
    """ send the message to online users """
    pass

# Some blocking functions
def block(username, client, client_ip, client_port):
    """ function to block account (username) from being logged in. """
    global BLOCKED_CLIENTS
    global block_time
    print(f"[BLOCK] Blocked access from {username}, IP: {client_ip}, PORT: {client_port}")
    BLOCKED_CLIENTS[username] = True

def is_blocked(username):
    """ returns true if user is currently blocked """
    global BLOCKED_CLIENTS
    return BLOCKED_CLIENTS[username]

def unblock(username):
    """ unblock the account(username) from the server """
    global BLOCKED_CLIENTS
    print(f"[BLOCK] Unblocked {username}")
    BLOCKED_CLIENTS[username] = False

def prompt_commands(client, username):
    """ prompt commands to user """
    global message
    while True:
        try:
            client.send('PROMPT_COMMANDS'.encode('utf-8'))
            message = client.recv(1024).decode()
            message = message.split(maxsplit=1)
            command = message[0]
            if command == 'MSG':
                message = message[1]
                broadcast(message)
            else:
                client.send('INVALID_COMMAND')
        except:
            print(f'[CONNECTION] {username} has disconnected')
            client_exit(client, username)
            broadcast('{username} has left the chat!'.encode('utf-8'))
            break

def prompt_login(client):
    """" prompt user to login """
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
            if is_blocked(username):
                    client.send('BLOCKED'.encode('utf-8'))
                    client.close()
            if logins[username] != password:  
                client.send('INCORRECT_PASSWORD'.encode('utf-8'))
                login_attempts += 1
            elif logins[username] == password:
                if username in USERNAMES:
                    client.send('ALREADY_LOGGED'.encode('utf-8'))
                    client.close()
                else:
                    login(client, username)
                    return (True, username)
        t_lock.notify()
        return (False, username)

def login(client, username):
    """ login the user to the chat client """
    global CURRENT_USERS
    global USERNAMES
    client.send('SUCCESS'.encode('utf-8'))
    CURRENT_USERS.append(client)
    USERNAMES.append(username)
    t_lock.notify()

def client_handler(client, addr):
    """ handles client interactions after receiving a connection """
    global t_lock
    global CURRENT_USERS
    global serverSocket
    client_ip = addr[0]
    client_port = addr[1]
    try:
        login_status = prompt_login(client)
        if login_status[0]:
            prompt_commands(client, login_status[1])
        else:
            client.send('BLOCK_LOGIN'.encode('utf-8'))
            block(login_status[1], client, client_ip, client_port)
            threading.Timer(block_time, unblock, [login_status[1]]).start()
            client.close()
    except:
        client.close()

def recv_handler():
    """ handles incomming connections """ 
    global serverSocket
    while True:
        client, addr = serverSocket.accept()
        print(f'[CONNECTION] connected with address {str(addr)}')
        client_thread = threading.Thread(target=client_handler, args=(client, addr))
        client_thread.start()

def send_handler():
    """ handles messaging for the server """
    global t_lock
    global CURRENT_USERS
    global serverSocket
    global message
    while True:
        # get lock
        with t_lock:
            
            t_lock.notify()

""" Initialize the server """
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