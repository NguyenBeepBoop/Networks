# Written by Nguyen Hoang z5257125
# Python --Version 3.9.1
import sys
from datetime import datetime
import re

MESSAGES = []
regexp='^[a-zA-Z0-9!@#$%.?,\s]+$'

def log_message(message, username):
    """ logs the message """
    global MESSAGES
    global messagelog
    global regexp
    dt = datetime.now().strftime("%d %b %Y %H:%M:%S")
    messageNo=len(MESSAGES) + 1
    # check if message sent has allowed chars
    if not re.match(regexp, message):
        return (False, messageNo, dt)
    edited="no"
    dic = {}
    dic["number"] = messageNo
    dic["user"] = username
    dic["message"] = message
    dic["time"] = dt
    dic["edited"] = edited
    # append message to a list of messages
    MESSAGES.append(dic)
    # log the message received
    messagelog.write(f"{messageNo}; {dt}; {username}; {message}; {edited}\n")
    messagelog.flush()
    print(f'> {username} posted MSG #{messageNo} "{message}" at {dt}.')
    return (True, messageNo, dt)

def delete_message(messageNumber, dt, username):
    """ deletes the message from the server given messageNumber, dateTime and username """
    global MESSAGES
    # check if message number exists
    if messageNumber > len(MESSAGES):
        return (False, "Message number does not exist.")
    message = MESSAGES[messageNumber-1]
     # check if the user is authorised and if messageNumber and dateTime combination exists
    if message['number'] == messageNumber and message['user'] == username and message['time'] == dt:
        dt = datetime.now().strftime("%d %b %Y %H:%M:%S")
        print(f'> {username} deleted MSG #{messageNumber} "{message["message"]}"" at {dt}.')
        MESSAGES.pop(messageNumber-1)
        write_messages()
        return (True, f"message #{messageNumber} deleted at {dt}.")
    else:
        errorMessage=""
        if message['user'] != username:
            errorMessage=f"Unauthorised to delete Message #{messageNumber}."
        else:
            errorMessage="Message Number and DateTime combination does not exist."
        return (False, errorMessage)

def edit_message(messageNumber, dt, newMessage, username):
    """ edits a message given messageNumber, datetime, username and new message """
    global MESSAGES
    global messagelog
    global regexp
    # check if message sent has allowed chars
    if not re.match(regexp, newMessage):
        return (False, "EDT: error: Invalid Message!")
    # check if message number exists
    elif messageNumber > len(MESSAGES):
        return (False, "Message number does not exist.")
    message = MESSAGES[messageNumber-1]
    # check if the user is authorised and if messageNumber and dateTime combination exists
    if message['number'] == messageNumber and message['user'] == username and message['time'] == dt:
        dt = datetime.now().strftime("%d %b %Y %H:%M:%S")
        print(f'> {username} edited MSG #{messageNumber} "{newMessage}" at {dt}.')
        message['message'] = newMessage
        message['edited'] = "yes"
        message['time'] = dt
        write_messages()
        return (True, f"message #{messageNumber} edited at {dt}.")
    else:
        errorMessage=""
        if message['user'] != username:
            errorMessage=f"Unauthorised to edit Message #{messageNumber}."
        else:
            errorMessage="Message Number and DateTime combination does not exist."
        return (False, errorMessage)

def get_messages(dt, username):
    res = []
    """ returns a list of messages given username and dateTime """
    # append all messages that the user did not post to list
    for message in MESSAGES:
        if message['user'] != username and message['time'] >= dt:
            string=f'#{message["number"]}; {message["user"]}: "{message["message"]}" posted at {message["time"]}.'
            res.append(string)
    if res:
        print("> Return messages:")
        for string in res:
            print(string.replace(";",""))
    return res

def write_messages():
    """ corrects the index of each message currently stored and writes to log file """
    global MESSAGES
    global messagelog
    messagelog.seek(0)
    messagelog.truncate()
    # fix the order of the message numbers and write to the log file
    for message in MESSAGES:
        message["number"] = MESSAGES.index(message) + 1
        messagelog.write(f"{message['number']}; {message['time']}; {message['user']}; {message['message']}; {message['edited']}\n")
    messagelog.flush()
messagelog = open("messages.txt", 'w')