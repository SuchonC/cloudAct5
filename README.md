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
For more detail of each handler function, I've already commented on the top of every function. Please review them

## Server (Lambda function)
This is the main body of the server. The behavior depends on parameters sent by client. Having extracted 'command' from the parameters, handler function is executed accordingly.
```python
def lambda_handler(event, context):
    params = event['queryStringParameters']
    if params['command']:
        if params['command'] == 'put' : 
            returnStatus = uploadfile(getDecodedBody(event), params)
            return getReturnDict(200, returnStatus)
        elif params['command'] == 'view' :
            files = viewFiles(params['user'])
            return getReturnDict(200, files)
        elif params['command'] == 'get' :
            file = downloadFile(params['filename'], params['user'])
            return getReturnDict(200, file)
```
Like for the client, details of every function are commented in the tops.