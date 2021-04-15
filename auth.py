# Written by Nguyen Hoang z5257125
# Python --Version 3.9.1
import sys
import datetime
BLOCKED_CLIENTS = {}
block_time = 10

def populate_logins():
    """ populate login data from credentials.txt to logins """ 
    global BLOCKED_CLIENTS
    user_logins = {}
    with open("credentials.txt", 'r') as file:
        for line in file:
            (username, password) = line.split()
            user_logins[username] = password
            BLOCKED_CLIENTS[username] = False
    file.close()
    return user_logins

logins = populate_logins()
userlog = open("userlog.txt", 'w')

# function to log interactions
def log_connection(username, addr, port, index):
    global userlog
    dt = datetime.datetime.now().strftime("%d %b %Y %H:%M:%S")
    userlog.write(f"{index}; {dt}; {username}; {addr}; {port};\n")
    userlog.flush()

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

def prompt_login(client, addr, ATTEMPTS, USERNAMES):
    """" prompt user to login """
    global logins
    while True:
        username = client.recv(1024).decode('utf-8')
        if username in logins:
            client.send('VALID_USERNAME'.encode('utf-8'))
            break
        else:
            client.send('INVALID_USERNAME'.encode('utf-8'))
    login_attempts = 0
    while login_attempts < ATTEMPTS:
        password = client.recv(1024).decode()
        if is_blocked(username):
                client.send('BLOCKED'.encode('utf-8'))
                client.close()
                break
        elif logins[username] != password and ATTEMPTS == 1:
            return (False, username)
        elif logins[username] != password:
            if login_attempts == 2:
                break
            else:
                client.send('INCORRECT_PASSWORD'.encode('utf-8'))
                login_attempts += 1
        elif logins[username] == password:
            if username in USERNAMES:
                client.send('ALREADY_LOGGED'.encode('utf-8'))
                client.close()
                break
            else:
                return (True, username)
    return (False, username)

logins = populate_logins()