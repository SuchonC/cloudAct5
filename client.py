from types import resolve_bases
import requests
import base64
import json

URL = "https://uuirpivhhc.execute-api.ap-southeast-1.amazonaws.com/default/cloudact5"
PATH = "D:\\CompEng\\Year 3\\Year 3 Term 2\\Cloud\\Activity 5\\codes\\files\\"

USER = "suchon1"

# takes splitted input into a dict
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
    elif input[0] == 'get' :
        if len(input) == 2 : # get filename of current user
            return {
                "arg0" : "get",
                "arg1" : input[1],
                "arg2" : USER
            }
        elif len(input) == 3:
            if input[2] != USER:
                print("Currently not available, please use \"get <filename> [Your Username]\"")
                return {}
            else :
                return { # same as "get" with no username specified
                    "arg0" : "get",
                    "arg1" : input[1],
                    "arg2" : USER
                }
        else :
            print("Usage : get <filename> [Username]")
            return {}

# handle put command
def handle_put(command_dict: dict) :
    filename = command_dict['arg1']
    try :
        with open(PATH + filename, 'rb') as file:
            response = requests.post(URL, data=file, params={
                "command": "put",
                "filename": filename,
                "user": USER
            }).json()
            if response['success'] : print("OK")
            else : print("FAILED")
    except FileNotFoundError:
        print(f"File {filename} not found")

# handle view command
def handle_view():
    try :
        response = requests.get(URL, params={
            "command": "view",
            "user": USER
        }).json()
        if response['success'] : print(f"OK\n{response['data']}")
        else : print("FAILED")
    except :
        print("FAILED")

def handle_get(command_dict: dict):
    filename = command_dict['arg1']
    user = command_dict['arg2']
    try:
        response = requests.get(URL, params={
            "command": "get",
            "filename": filename,
            "user": user
        }).json()
        if response['success'] :
            print("OK")
            with open(PATH + filename, 'wb') as file:
                file.write(base64.b64decode(response['data']))
        else :
            print(f"FAILED, {response['data']}")
    except:
        print("FAILED")

while True:
    user_input = input(">> ").split()
    command = decodeInput(user_input)
    if command : # if command is valid then execute command
        if command['arg0'] == 'put' : handle_put(command)
        elif command['arg0'] == 'view' : handle_view()
        elif command['arg0'] == 'get' : handle_get(command)