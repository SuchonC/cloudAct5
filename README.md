# Cloud Activity 5
Dropbox-like command line with client and server writted in Python

## Client
This is the main loop which calls handler functions according to the command recieved
``` python
while True:
    user_input = input(">> ").split()
    command = decodeInput(user_input)
    if command :
        if command['arg0'] == 'put' : handle_put(command) 
        elif command['arg0'] == 'view' : handle_view()
        elif command['arg0'] == 'get' : handle_get(command)
```