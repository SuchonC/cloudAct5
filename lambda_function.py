import json
import boto3
import base64

s3 = boto3.client('s3')
db = boto3.client('dynamodb')
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
# checking a file ownership
# by looking up in 'Files' table in DynamoDB for 'username' and 'filename'
def isOwnerOfFile(user: str, filename: str) -> bool :
    result = db.query(
        TableName="Files",
        Select="COUNT",
        KeyConditionExpression="username = :a AND filename = :b",
        ExpressionAttributeValues={
            ":a" : {"S" : user},
            ":b" : {"S" : filename}
        }
    )
    return result['Count'] > 0

# Helper function
# checking whether a file is shared with that specific user
# by looking up in 'Sharings' table in DynamoDB for 'share_to' and 'filename'
def isSharedWith(user: str, encoded_filename: str) -> bool :
    result = db.query(
        TableName="Sharings",
        Select="COUNT",
        KeyConditionExpression="shared_to = :a AND filename = :b",
        ExpressionAttributeValues={
            ":a" : {"S" : user},
            ":b" : {"S" : encoded_filename}
        }
    )
    return result['Count'] > 0

# Helper function
# check whether an input username already exists
# by looking up in the 'Users' table in DynamoDB for 'username'
def isUsernameExists(username: str) -> bool :
    response = db.query(
        TableName="Users",
        Select="COUNT",
        KeyConditionExpression='username = :a',
        ExpressionAttributeValues={
            ':a': {'S': username}
        }
    )
    return response['Count'] > 0

# Helper function
# Returns a list of filenames owned by an input username
# By looking up in the 'Files' table
def getFilenamesOwnedBy(username: str) :
    owned_by = db.query(
        TableName="Files",
        KeyConditionExpression="username = :a",
        ProjectionExpression="filename",
        ExpressionAttributeValues={
            ":a" : {"S" : username}
        }
    )
    filenames = []
    for file in owned_by['Items'] :
        filenames.append(file['filename']['S'])
    return filenames

# Helper function
# Returns a list of {'filename': <filename>, 'owner': <the person who shared this file>}
# By looking up in the 'Sharings' table
def getFilenamesSharedWith(username: str) :
    shared_with = db.query(
        TableName="Sharings",
        KeyConditionExpression="shared_to = :a",
        ExpressionAttributeValues={
            ":a" : {"S" : username}
        }
    )
    filenames = []
    for file in shared_with['Items'] :
        filename = file['filename']['S']
        owner = file['shared_from']['S']
        filenames.append({
            "filename" : decodeFileName(filename, owner),
            "owner" : owner
        })
    return filenames

# Handles uploading file
# takes in "file" (in byte) and "params" as arguments
# expected params structure is {'filename': <filename>, 'user': <file owner>}
# upload "file" to s3 with encoded name as a Key (using previously described function)
def uploadfile(file, params: dict) :
    encoded_filename = encodeFileName(params['filename'], params['user'])
    try :
        db.put_item(
            TableName="Files",
            Item={
                "username" : {"S" : params['user']},
                "filename" : {"S" : params['filename']}
            }
        )
        s3.put_object(Body=file, Key=encoded_filename, Bucket=BUCKET_NAME)
        return json.dumps({
            "success" : True
        })
    except :
        return json.dumps({
            "success" : False
        })

# Handles viewing files
# outputs files owned by or shared with "user" in string
def viewFiles(user: str) :
    files_owned_by = getFilenamesOwnedBy(user)
    files_shared_with = getFilenamesSharedWith(user)
    output = ''
    for file in files_owned_by:
        encoded_filename = encodeFileName(file, user)
        object = s3.head_object(Bucket=BUCKET_NAME, Key=encoded_filename)
        file_size = str(object['ContentLength'])
        last_modified = object['LastModified']
        output += f"{file} {file_size} {last_modified} {user}\n"
        print(object['LastModified'])
    for record in files_shared_with:
        encoded_filename = encodeFileName(record['filename'], record['owner'])
        object = s3.head_object(Bucket=BUCKET_NAME, Key=encoded_filename)
        file_size = str(object['ContentLength'])
        last_modified = object['LastModified']
        output += f"{record['filename']} {file_size} {last_modified} {record['owner']}\n"
    return json.dumps({
        "success" : True,
        "data" : output[:-1]
    })

# Handles downloading file
# takes in "filename" and "user" as arguments
# then check if "user" owns/shared with that "filename"
# if yes, then return base 64 encoded file with encoding flag set
# if no, return error message in "data"
def downloadFile(filename: str, user: str) :
    encoded_filename = encodeFileName(filename, user)
    if isOwnerOfFile(user, filename) or isSharedWith(user, encoded_filename) :
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

# Handles creating user
# takes in username and password as function arguments
# then put an item in 'Users' table accordingly
def createUser(username: str, password: str) :
    if not isUsernameExists(username):
        db.put_item(
            TableName="Users",
            Item={
                "username" : {"S" : username},
                "password" : {"S" : password}
            }
        )
        return json.dumps({
            "success" : True
        })
    else : return json.dumps({
        "success" : False,
        "data" : f"Username \"{username}\" is already exists"
    })

# Handles login
# takes in username and password
# then query 'Users' table to record with the input username and password
# return true if record count equals 1
def login(username: str, password: str) :
    response = db.query(
        TableName="Users",
        Select="COUNT",
        KeyConditionExpression='username = :a',
        FilterExpression="password = :b",
        ExpressionAttributeValues={
            ':a': {'S': username},
            ':b': {'S': password}
        }
    )
    return json.dumps({
        "success" : response['Count'] == 1
    })
    
# Handles sharing
# takes in 'share_from_user' (user who executes 'share' command)
#          'share_to_user' (username of the user that the file will be shared with)
#          'filename' (name of the file to be shared)
# validations : 1. share_from_user must exists 2. share_from_user must be the owner of file
# then put a record in the 'Sharings' table accordingly
def share(share_from_user: str, share_to_user: str, filename: str) :
    # share_to_user must exists
    if not isUsernameExists(share_to_user) :
        return json.dumps({
            "success" : False,
            "data" : f"Username \"{share_to_user}\" does not exists"
        })
    # filename must be owned by share_from_user ?? or can one share files that one has been shared with
    if not isOwnerOfFile(share_from_user, filename) :
        return json.dumps({
            "success" : False,
            "data" : f"{filename} is not owned by you"
        })
    db.put_item(
        TableName="Sharings",
        Item={
            "shared_to" : {"S" : share_to_user},
            "shared_from" : {"S" : share_from_user},
            "filename" : {"S" : encodeFileName(filename, share_from_user)}
        }
    )
    return json.dumps({
        "success" : True
    })

def lambda_handler(event, context):
    # main
    params = event['queryStringParameters'] # get parameter dict
    if params['command']: # execute commands by comparing "command"
        if params['command'] == 'put' : 
            returnStatus = uploadfile(getDecodedBody(event), params)
            return getReturnDict(201, returnStatus)
        elif params['command'] == 'view' :
            files = viewFiles(params['user'])
            return getReturnDict(200, files)
        elif params['command'] == 'get' :
            file = downloadFile(params['filename'], params['user'])
            return getReturnDict(200, file)
        elif params['command'] == 'newuser' :
            newuser = createUser(params['username'], params['password'])
            return getReturnDict(201, newuser)
        elif params['command'] == 'login' :
            loginStatus = login(params['username'], params['password'])
            return getReturnDict(201, loginStatus)
        elif params['command'] == 'share' :
            shareStatus = share(params['share_from'], params['share_to'], params['filename'])
            return getReturnDict(201, shareStatus)