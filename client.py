# Written by Nguyen Hoang z5257125
# Python --Version 3.9.1
from socket import *
import threading
import select
import sys
import time
import signal
import json

serverMessage = ""
message = ""
command = ""
running = True
timeout = 2

def keyboard_interrupt_handler(signal, frame):
    global clientSocket
    print("\r[SHUTDOWN] Connection to server has been closed.")
    clientSocket.close()
    sys.exit(1)

def client_exit(clientSocket):
    """ terminates the socket and closes the client program """
    global running
    clientSocket.close()
    running=False
    sys.exit(1)

def p2p_recv_handler():
    """ handles incoming p2p connections """
    global p2pSocket
    global running
    global timeout
    while running:
        # listen for data being transferred by other clients
        data, addr = p2pSocket.recvfrom(2048)
        # if receiving a file
        if data:
            fileName = data.strip()
            f = open(fileName, 'wb')
            fileName = data.decode()
            data, addr = p2pSocket.recvfrom(2048)
            username = data.decode()
            # read bytes received and write to file
            while True:
                """ 
                timeout implementation inspired by stackoverflow approach using select() to
                wait until data is available or timeout occurs.
                socket.settimeout could have also been used but this is much nicer.
                https://stackoverflow.com/questions/2719017/how-to-set-timeout-on-pythons-socket-recv-method
                """
                ready = select.select([p2pSocket], [], [], timeout)
                if ready[0]:
                    data, addr = p2pSocket.recvfrom(2048)
                    f.write(data)
                else:
                    print(f"\n> Received {fileName} from {username}")
                    print("> Enter one of the following commands (MSG, DLT, EDT, RDM, ATU, OUT, UPD):", end=" ")
                    sys.stdout.flush()
                    f.close()
                    break

def p2p_send(username, fileName, addr, port):
    """ makes a UDP connection to server given addr and port, sends then file given """
    # create a socket to connect to the client p2p server
    p2pClientSocket = socket(AF_INET, SOCK_DGRAM)
    p2pClientSocket.sendto(fileName.encode(), (addr, port))
    p2pClientSocket.sendto(username.encode(), (addr, port))
    # open the file to be transferred
    f = open(fileName, "rb")
    data = f.read(2048)
    print(f'sending {fileName}')
    while (data):
        if(p2pClientSocket.sendto(data, (addr, port))):
            data = f.read(2048)
            time.sleep(0.02)
    p2pClientSocket.close()
    f.close()

def recv_handler():
    """ handles incoming packets from the TCP server"""
    global clientSocket
    global serverMessage
    global message
    global command
    global running
    global p2pSocket
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
            elif command == 'UPD':
                peerData = data['message']
                fileName = data['filename']
                username = data['username']
                addr = peerData[0]
                port = peerData[1]
                p2p_send(username, fileName, addr, port)
            else:
                print(command)
        except:
            # Close Connection When Error
            client_exit(clientSocket)
            break

def send_handler():
    """ handles sending of data to the TCP server """
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
    """ starts the client interface """
    global running
    print("Welcome to Toom!")
    recv_thread = threading.Thread(target=recv_handler)
    recv_thread.daemon = False
    recv_thread.start()

    send_thread = threading.Thread(target=send_handler)
    send_thread.daemon = False
    send_thread.start()

    p2p_recv_thread = threading.Thread(target=p2p_recv_handler)
    p2p_recv_thread.daemon = True
    p2p_recv_thread.start()

    while running:
        time.sleep(0.1)

def login():
    """ logs in client to the server specified """
    global clientSocket
    global running
    while True:
        # send username to server
        clientSocket.send(input("> Username: ").encode('utf-8'))
        usernameStatus = clientSocket.recv(1024).decode('utf-8')
        if usernameStatus == 'INVALID_USERNAME':
            print("> Please enter a valid username.")
        elif usernameStatus == 'VALID_USERNAME':
            break
    # send password to server
    clientSocket.send(input("> Password: ").encode('utf-8'))
    while True:
        try:
            # get login result from server
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

if __name__ == "__main__":
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

    p2pSocket = socket(AF_INET, SOCK_DGRAM)
    p2pSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    IP = clientSocket.getsockname()[0]
    PORT = clientSocket.getsockname()[1]
    p2pSocket.bind((IP, PORT))

    signal.signal(signal.SIGINT, keyboard_interrupt_handler)
    login()