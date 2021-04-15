# Written by Nguyen Hoang z5257125
# Python --Version 3.9.1
import sys
from socket import *
from user import User
import auth
import threading
import message
import time
import datetime
import signal
import json
import re

CLIENTS = []
USERS = []
UPDATE_INTERVAL = 1
IP = 'localhost'
block_time=10
t_lock=threading.Condition()
# Get the server port and attempts allowed for login
try:
    PORT = int(sys.argv[1])
    ATTEMPTS = int(sys.argv[2])
    if PORT < 1024:
        print("Port number must be greater than 1024!")
        sys.exit(1)
    elif ATTEMPTS > 5 or ATTEMPTS < 1:
        print("Attempts must be between 1 and 5!")
        sys.exit(1)
except:
    print("Usage: Python3 server.py <PORT> <ATTEMPTS>")
    sys.exit(1)

serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
serverSocket.bind((IP, PORT))

def client_exit(client, user):
    """ close the connection to the client and remove the client from current users """
    global CLIENTS
    global USERS
    global t_lock
    with t_lock:
        CLIENTS.remove(client)
        USERS.remove(user)
        print(f'> {user.getUsername()} logout')
        client.send(json.dumps({
                'command': 'OUT',
                'message': f"Bye, {user.getUsername()}!"
            }).encode("utf-8"))
        client.close()
        t_lock.notify()

def keyboard_interrupt_handler(signal, frame):
    """ print a shutdown message if server is closed with CTRL+C """
    print("\r[SHUTDOWN] Server has been shutdown")
    sys.exit(0)

def getUsernames():
    global USERS
    res=[]
    for user in USERS:
        res.append(user.getUsername())
    return res

def getActiveUsersList(username):
    res = []
    for user in USERS:
        if user.getUsername() != username:
            string=f"{user.getUsername()}, {user.getAddr()}, {user.getPort()}, active since {user.getLastActive()}."
            res.append(string)
    if not res:
        print("> No other active users")
        return res
    else:
        print("> Return active user list:")
        for user in res:
            print(user.replace(',',';'))
        return res

def login(client, username, addr, port):
    """ appends client and user to a list """
    global CLIENTS
    # use lock as we are accesing data structures
    with t_lock:
        client.send('SUCCESS'.encode('utf-8'))
        dt = datetime.datetime.now().strftime("%d %b %Y %H:%M:%S")
        CLIENTS.append(client)
        index=CLIENTS.index(client) + 1
        user=User(username, addr, port, dt)
        USERS.append(user)
        auth.log_connection(username, addr, port, index)
        t_lock.notify()
    return user

def prompt_commands(client, user):
    global USERS
    """ prompt commands to user """
    while True:
        try:
            client.send(json.dumps({'command': 'PROMPT_COMMANDS'}).encode('utf-8'))
            data = client.recv(1024).decode("utf-8")
            data = data.split(maxsplit=1)
            command = data[0]
            with t_lock:
                if command == 'MSG':
                    # if there are invalid args supplied send error message
                    if len(data) != 2:
                        client.send(json.dumps({
                            'command': 'PRINT',
                            'message': "MSG: error: Invalid Message!"
                        }).encode("utf-8"))
                    else: # otherwise log the message to the server if the message format is valid
                        res = message.log_message(data[1], user.getUsername())
                        # send a success message to the client to confirm message has been posted
                        if (res[0]):
                            client.send(json.dumps({
                                'command': 'PRINT',
                                'message': f"Message #{res[1]} posted at {res[2]}"
                            }).encode("utf-8"))
                        else:
                            client.send(json.dumps({
                                'command': 'PRINT',
                                'message': "MSG: error: Invalid Message!"
                            }).encode("utf-8"))
                elif command == 'EDT':
                    messageInfo = data[1].split()
                    # if there are invalid args supplied
                    if len(messageInfo) < 6:
                        client.send(json.dumps({
                                    'command': 'PRINT',
                                    'message': "usage: EDT <messageNumber> <dateTime> <newMessage>"
                                }).encode("utf-8"))
                    else:
                        messageNumber = int(re.findall('\d+',messageInfo[0])[0])
                        date = ' '.join(messageInfo[1:5])
                        newMessage=' '.join(messageInfo[5:])
                        # try to edit the message
                        res = message.edit_message(messageNumber, date, newMessage, user.getUsername())
                        client.send(json.dumps({
                                    'command': 'PRINT',
                                    'message': f"{res[1]}"
                                }).encode("utf-8"))
                elif command == 'DLT':
                    messageInfo = data[1].split(maxsplit=1)
                    if len(messageInfo) < 2:
                        client.send(json.dumps({
                                    'command': 'PRINT',
                                    'message': "usage: DLT <messageNumber> <dateTime>"
                                }).encode("utf-8"))
                    else:
                        messageNumber = int(re.findall('\d+',messageInfo[0])[0])
                        date = messageInfo[1]
                        res = message.delete_message(messageNumber, date, user.getUsername())
                        client.send(json.dumps({
                                    'command': 'PRINT',
                                    'message': f"{res[1]}"
                                }).encode("utf-8"))
                elif command == 'RDM':
                    print(f"> {user.getUsername()} issued RDM command.")
                    if len(data) < 2:
                        client.send(json.dumps({
                                    'command': 'PRINT',
                                    'message': "RDM: error: Please specify a date to read from."
                                }).encode("utf-8"))
                    else:
                        date=data[1]
                        res=message.get_messages(date, user.getUsername())
                        if res:
                            client.send(json.dumps({
                                    'command': 'RDM',
                                    'message': res
                                }).encode("utf-8"))
                        else:
                            client.send(json.dumps({
                                    'command': 'PRINT',
                                    'message': "No new message."
                                }).encode("utf-8"))
                elif command == 'ATU':
                    # print message to show server has received ATU request
                    print(f"> {user.getUsername()} issued ATU command ATU.")
                    # get the active users list
                    res = getActiveUsersList(user.getUsername())
                    # if there are other active users send the list to the client
                    if res:
                        client.send(json.dumps({
                                    'command': 'ATU',
                                    'message': res
                                }).encode("utf-8"))
                    # otherwise notify client of no other active users
                    else:
                        client.send(json.dumps({
                                    'command': 'PRINT',
                                    'message': "No other active users."
                                }).encode("utf-8"))
                elif command == 'UPD':
                    continue
                elif command == 'OUT':
                    client_exit(client, user)
                    break
                else:
                    client.send(json.dumps({'command': 'INVALID_COMMAND'}).encode('utf-8'))
                t_lock.notify()
        except:
            client_exit(client, user)
            break

def client_handler(client, addr):
    """ handles client interactions after receiving a connection """
    global t_lock
    global serverSocket
    global ATTEMPTS
    client_ip = addr[0]
    client_port = addr[1]
    try:
        login_status = auth.prompt_login(client, addr, ATTEMPTS, getUsernames())
        if login_status[0]:
            user = login(client, login_status[1], client_ip, client_port)
            prompt_commands(client, user)
        else:
            client.send('BLOCK_LOGIN'.encode('utf-8'))
            auth.block(login_status[1], client, client_ip, client_port)
            threading.Timer(block_time, auth.unblock, [login_status[1]]).start()
            client.close()
    except:
        client.close()

def recv_handler():
    """ handles incomming connections """ 
    global serverSocket
    while True:
        client, addr = serverSocket.accept()
        print(f'[CONNECTION] User connected with address {str(addr)}')
        # start thread for client joining
        client_thread = threading.Thread(target=client_handler, args=(client, addr))
        client_thread.start()

print("[STARTING] server is starting...")

serverSocket.listen(1)
print("[READY] Server is ready for service")
print("Running on http://127.0.0.1:" + str(PORT) + "/")
recv_thread = threading.Thread(name="RecvHandler", target=recv_handler)
recv_thread.daemon = True
recv_thread.start()

signal.signal(signal.SIGINT, keyboard_interrupt_handler)

while True:
    time.sleep(0.1)