import requests
import base64
import os
import pathlib

if not 'LAMBDA_URL' in os.environ :
    print("Please set an environment variable named 'LAMBDA_URL' with the my URL. You can find it in my PDF")
    exit()

URL = os.environ['LAMBDA_URL']
PATH = pathlib.Path().absolute() # files to be used are located in 'files' subfolder
USER = ""

# takes splitted input into a dict
# ex. from ['put', 'myfile.txt'] into {'arg0: 'put', 'arg1': 'myfile.txt'}
def decodeInput(input: list) -> dict:
    if type(input) != list :
        print("Input to validate must be a list")
        return {}
    if input[0] == 'put' : # if command is put
        if len(input) != 2 :
            print("Usage: put <filename>")
            return {}
        return {
            "arg0" : "put",
            "arg1" : input[1]
        }
    elif input[0] == 'view' : # if command is view
        if len(input) != 1 :
            print("Usage: view")
            return {}
        return {
            "arg0" : "view"
        }
    elif input[0] == 'get' : # if command is get
        if len(input) == 2 : # get filename of current user
            return {
                "arg0" : "get",
                "arg1" : input[1],
                "arg2" : USER
            }
        elif len(input) == 3:
            return {
                "arg0" : "get",
                "arg1" : input[1],
                "arg2" : input[2]
            }
        else :
            print("Usage : get <filename> [Username]")
            return {}
    elif input[0] == 'newuser' : # if command is newuser
        if len(input) == 4:
            return {
                "arg0" : "newuser",
                "arg1" : input[1],
                "arg2" : input[2],
                "arg3" : input[3]
            }
        else :
            print("Usage : newuser <username> <password> <confirm password>")
            return {}
    elif input[0] == 'login' : # if command is login
        if len(input) == 3 :
            return {
                "arg0" : "login",
                "arg1" : input[1],
                "arg2" : input[2]
            }
        else :
            print("Usage : login <username> <password>")
            return {}
    elif input[0] == 'share' : # if command is share
        if len(input) == 3 :
            return {
                "arg0" : "share",
                "arg1" : input[1],
                "arg2" : input[2]
            }
        else :
            print("Usage : share <filename> <destination username>")
            return
    elif input[0] == 'logout' : # if command is logout
        if len(input) == 1 :
            return {
                "arg0" : "logout"
            }
        else :
            print("Usage : logout")
    elif input[0] == 'quit' :
        exit()
    else : print("List of commands : newuser, login, logout, share, put, view, get and exit")

def isLoggedIn():
    return USER != ''

# handle put command
# takes in {'arg0': 'put', 'arg1': <filename>}
# then send post request to lambda with file (in byte) as a request body
# and {'command': 'put', 'filename': <filename>, 'user': <user>} as a request parameter
# expected {'success': True | False} as a response
def handle_put(command_dict: dict) :
    if not isLoggedIn():
        print("Please login")
        return
    filename = command_dict['arg1']
    try :
        with open(PATH.joinpath(filename), 'rb') as file:
            response = requests.post(URL, data=file, params={
                "command": "put",
                "filename": filename,
                "user": USER
            }).json()
            if response['success'] : print("OK")
            else : print("FAILED")
    except FileNotFoundError: # if file is not found
        print(f"File {filename} not found")

# handle view command
# takes in nothing
# then send get request to lambda with an empty request body
# and {'command': 'view', 'user': <user>} as a request parameter
# expected {'success': True | False, 'data': <list of files in string>} as a response
def handle_view():
    if not isLoggedIn():
        print("Please login")
        return
    try :
        response = requests.get(URL, params={
            "command": "view",
            "user": USER
        }).json()
        if response['success'] : print(f"OK\n{response['data']}")
        else : print("FAILED")
    except :
        print("FAILED")

# handle get command
# takes in {'arg0': 'get', 'filename': <filename>. 'user': <user>}
# then send a get requet to lambda with an empty request body
# and {'commnand': 'get', 'filename': <filename>, 'user': <user>} as a request parameter
# expected {'success': True | False, 'data': <file | failed message>, 'isBase64Encoded': True | False} as a response
def handle_get(command_dict: dict):
    if not isLoggedIn():
        print("Please login")
        return
    filename = command_dict['arg1']
    user = command_dict['arg2']
    try:
        response = requests.get(URL, params={
            "command": "get",
            "filename": filename,
            "user": user
        }).json()
        if response['success'] :
            with open(PATH.joinpath(filename), 'wb') as file:
                # check encoding flag
                if response['isBase64Encoded'] :
                    file.write(base64.b64decode(response['data']))
                else : file.write(response['data'])
                print("OK")
        else :
            print(f"FAILED, {response['data']}")
    except FileNotFoundError:
        print(f"FAILED, {PATH} not found")

# handle newuser command
# send POST request with username and password to be created as request parameters
# expected response {'success': True | False, 'data': <failed message>}
def handle_newuser(command_dict: dict) :
    # validate password (confirm)
    if command_dict['arg2'] != command_dict['arg3'] :
        print("Passwords do not match")
    else :
        response = requests.post(URL, params={
            "command" : "newuser",
            "username" : command_dict['arg1'],
            "password" : command_dict['arg2']
        }).json()
        if response['success'] : print("OK")
        else : print(f"FAILED\n{response['data']}")

# handle login command
# send POST request with username and password to be logged in as request parameters
# expected response {'success': True | False}
def handle_login(command_dict: dict) :
    response = requests.post(URL, params={
        "command" : "login",
        "username" : command_dict['arg1'],
        "password" : command_dict['arg2']
    }).json()
    if response['success'] :
        print("OK")
        global USER
        USER = command_dict['arg1']
    else : print("FAILED")


# handle share command
# send POST request to share a file with the following structure
# {
#   'command': 'share',
#   'share_from': <current_user>,
#   'share_to': <destination_user>,
#   'filename': <filename_to_be_shared>
# }
# expected response {'success': True | False, 'data': <failed message>}
def handle_share(command_dict: dict) :
    if not isLoggedIn() :
        print("Please login")
        return
    response = requests.post(URL, params={
        "command" : "share",
        "share_from" : USER,
        "share_to" : command_dict['arg2'],
        "filename" : command_dict['arg1']
    }).json()
    if response['success'] : print("OK")
    else :
        print(f"FAILED\n{response['data']}")

# handle logout command
# basically just set USER to ''
# empty USER variable, that is
def handle_logout(command_dict: dict) :
    if not isLoggedIn() :
        print("Please login")
        return
    global USER
    USER = ''
    print("OK")

# main loop
while True:
    user_input = input(">>").split() # split the input
    command = decodeInput(user_input) # decode splitted input into a dict
    if command : # if input is successfully decoded then execute command by comparing 'arg0'
        if command['arg0'] == 'put' : handle_put(command) 
        elif command['arg0'] == 'view' : handle_view()
        elif command['arg0'] == 'get' : handle_get(command)
        elif command['arg0'] == 'newuser' : handle_newuser(command)
        elif command['arg0'] == 'login' : handle_login(command)
        elif command['arg0'] == 'share' : handle_share(command)
        elif command['arg0'] == 'logout' : handle_logout(command)