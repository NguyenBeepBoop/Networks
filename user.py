# Written by Nguyen Hoang z5257125
# Python --Version 3.9.1
import sys
import datetime

""" A simple class for user. """
class User:
    def __init__(self, username, addr, port, lastActive):
        self.username = username
        self.addr = addr
        self.port = port
        self.lastActive = lastActive

    def getUsername(self):
        return self.username

    def getAddr(self):
        return self.addr
    
    def getPort(self):
        return self.port

    def getLastActive(self):
        return self.lastActive

    def setLastActive(self, dt):
        self.lastActive = dt