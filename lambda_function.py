import json
import boto3
import base64

s3 = boto3.client('s3')
BUCKET_NAME = "cloudact5"

# Helper function
# outputs a dict which would then be returned to the client
def getReturnDict(code: int, body) :
    return {
        "statusCode" : code,
        "body" : body
    }

# Helper function
# decode event['body'] if encoding flag is set
def getDecodedBody(event: dict) : 
    if(event['isBase64Encoded']) : return base64.b64decode(event['body'])
    else : return event['body']

# Helper function
# prepend '[owner] - ' to filename 
# ex. filename is "myfile.txt" and owner is "suchon"
# then it outputs "[suchon] - myfile.txt"
# this handles the scenario when different users have the same filename
def encodeFileName(filename: str, owner: str) :
    return f"[{owner}] - {filename}"
    
# Helper function
# the opposite of encoding filename
# ex. filename is "[suchon] - myfile.txt" and owner is "suchon"
# then it outputs "myfile.txt"
def decodeFileName(filename: str, owner: str) :
    cut_length = len(owner) + 5
    return filename[cut_length:]
    
# Helper function
# checking file ownership
# by taking encoded filename and a user to check ownership with as arguments
# get metadata of "encoded_filename" and compare "owner" with the user argument
def isOwnerOfFile(user: str, encoded_filename: str) -> bool :
    try: 
        owner = s3.head_object(Bucket=BUCKET_NAME, Key=encoded_filename)['Metadata']['owner']
        return owner == user
    except:
        return False

# Handles uploading file
# takes in "file" (in byte) and "params" as arguments
# expected params structure is {'filename': <filename>, 'user': <file owner>}
# upload "file" to s3 with encoded name as a Key (using previously described function)
# with 'owner' as metadata
def uploadfile(file, params: dict) :
    encoded_filename = encodeFileName(params['filename'], params['user'])
    try :
        s3.put_object(Body=file, Key=encoded_filename, Bucket=BUCKET_NAME, Metadata={
            "owner": params['user']
        })
        return json.dumps({
            "success" : True
        })
    except :
        return json.dumps({
            "success" : False
        })

# Handles viewing files
# outputs files owned by "user" in string
# output ex. "file1.txt 15 2021/02/20 16:21:12\ntest2.txt 15 2021/02/20 16:00:23"
def viewFiles(user: str) :
    files_str = ''
    dict_result =  s3.list_objects(Bucket=BUCKET_NAME)
    if 'Contents' in dict_result:
        objects = dict_result['Contents']
        for i in range (len(objects)):
            encoded_filename = objects[i]['Key']
            if isOwnerOfFile(user, encoded_filename) :
                decoded_filename = decodeFileName(encoded_filename, user)
                file_size = str(objects[i]['Size'])
                last_modified = objects[i]['LastModified'].strftime("%Y/%m/%d %H:%M:%S")
                files_str += f"{decoded_filename} {file_size} {last_modified}\n"
    return json.dumps({
        "success" : True,
        "data" : files_str[:-1]
    })

# Handles downloading file
# takes in "filename" and "user" as arguments
# then check if "user" owns that "filename"
# if yes, then return base 64 encoded file with encoding flag set
# if no, return error message in "data"
def downloadFile(filename: str, user: str) :
    encoded_filename = encodeFileName(filename, user)
    if isOwnerOfFile(user, encoded_filename) :
        data_byte = s3.get_object(Bucket=BUCKET_NAME, Key=encoded_filename)['Body'].read()
        return json.dumps({
            "success" : True,
            "data" : base64.b64encode(data_byte).decode('utf-8'),
            "isBase64Encoded" : True
        })
    else : return json.dumps({
        "success" : False,
        "data" : f"{filename} does not belong to {user}",
        "isBase64Encoded" : False
    })

def lambda_handler(event, context):
    # main
    params = event['queryStringParameters'] # get parameter dict
    if params['command']: # execute commands by comparing "command"
        if params['command'] == 'put' : 
            returnStatus = uploadfile(getDecodedBody(event), params)
            return getReturnDict(200, returnStatus)
        elif params['command'] == 'view' :
            files = viewFiles(params['user'])
            return getReturnDict(200, files)
        elif params['command'] == 'get' :
            file = downloadFile(params['filename'], params['user'])
            return getReturnDict(200, file)