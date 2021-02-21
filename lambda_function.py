import json
import boto3
import base64

s3 = boto3.client('s3')
BUCKET_NAME = "cloudact5"

# Helper function
def getDecodedBody(event: dict) : 
    if(event['isBase64Encoded']) : return base64.b64decode(event['body'])
    else : return event['body']

# Helper function
# prepend '[owner] - ' to filename 
def encodeFileName(filename: str, owner: str) :
    return f"[{owner}] - {filename}"
    
# Helper function
def decodeFileName(filename: str, owner: str) :
    cut_length = len(owner) + 5
    return filename[cut_length:]
    
# Helper function
def isOwnerOfFile(user: str, encoded_filename: str) -> bool :
    try: 
        owner = s3.head_object(Bucket=BUCKET_NAME, Key=encoded_filename)['Metadata']['owner']
        return owner == user
    except:
        return False
    
def uploadfile(file, params: dict) :
    encoded_filename = encodeFileName(params['filename'], params['user'])
    try :
        s3.put_object(Body=file, Key=encoded_filename, Bucket=BUCKET_NAME, Metadata={
            "owner": params['user'],
            "filename": params['filename']
        })
        return json.dumps({
            "success" : True
        })
    except :
        return json.dumps({
            "success" : False
        })
        
def viewFiles(user: str) :
    owner = user
    files_str = ''
    objects =  s3.list_objects(Bucket=BUCKET_NAME)['Contents']
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
    
def getReturnDict(code: int, body) :
    return {
        "statusCode" : code,
        "body" : body
    }

def lambda_handler(event, context):
    # test case
    # decoded_body = event
    # params = {
    #     "command": "view",
    #     "user": "suchon1"
    # }
    # ------------

    params = event['queryStringParameters']
    
    if params['command']:
        if params['command'] == 'put' : 
            # returnStatus = uploadfile(event, params)
            returnStatus = uploadfile(getDecodedBody(event), params)
            return getReturnDict(200, returnStatus)
        elif params['command'] == 'view' :
            files = viewFiles(params['user'])
            return getReturnDict(200, files)
        elif params['command'] == 'get' :
            file = downloadFile(params['filename'], params['user'])
            return getReturnDict(200, file)