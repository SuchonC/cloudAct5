# Cloud Activity 5
Dropbox-like command line with client and server writted in Python

## Client
Set your API Gateway (HTTP) in environment variable named "LAMBDA_URL" then execute the following command
> python client.py

## Server (Lambda function)
Waits for client requests. Response behavior depends on request parameter and body
