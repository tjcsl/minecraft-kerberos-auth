from flask import Flask, request, render_template, send_file
import json
import sqlite3
import uuid
app = Flask(__name__)
conn = sqlite3.connect('auth.db', check_same_thread = False)
c = conn.cursor()
######## DB SCHEMA #########
""" CREATE TABLE users(
ID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
username TEXT NOT NULL,
accessToken TEXT NOT NULL,
clientToken TEXT NOT NULL 
); """

################## Errors ##################
def method_not_allowed():
    args = {"error":"Method Not Allowed","errorMessage":"The method specified in the request is not allowed for the resource identified by the request URI"}
    return json.dumps(args), 405

def invalid_credentials_migrated():
    args = {"error":"ForbiddenOperationException","errorMessage":"Invalid credentials. Account migrated, use e-mail as username.","cause":"UserMigratedException"}
    return json.dumps(args), 403

def invalid_credentials():
    args = {"error":"ForbiddenOperationException","errorMessage":"Invalid credentials. Invalid username or password."}
    return json.dumps(args), 403

def invalid_token():
    args = {"error":"ForbiddenOperationException","errorMessage":"Invalid token."}
    return json.dumps(args), 403

def illegal_argument_exception():
    args = {"error":"IllegalArgumentException","errorMessage":"Access token already has a profile assigned."}
    return json.dumps(args)

def unsupported_media_type():
    args = {"error":"Unsupported Media Type","errorMessage":"The server is refusing to service the request because the entity of the request is in a format not supported by the requested resource for the requested method"}
    return json.dumps(args), 415

def custom_exception(args):
    return json.dumps(args), 400
    
################## Authentication Methods ##
def validate_user(username, password):
    print(username,password)
    from subprocess import Popen, PIPE
    from time import sleep
    kinit = '/usr/bin/kinit'
    realm = "LOCAL.TJHSST.EDU"
    kinit_args = [kinit, '%s@%s' % (username, realm)]
    kinit = Popen(kinit_args, stdin=PIPE)
    #sleep(1)
    kinit.stdin.write('%s\n' % password)
    e = kinit.wait()
    #out,err = kinit.communicate()
    #print(out,err)
    return not e
################## Endpoints ###############

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return send_file("index.html")
    return method_not_allowed()

@app.route('/authenticate', methods=['GET', 'POST'])
def authenticate():
    if request.method == 'GET':
        return method_not_allowed()
    if request.mimetype != 'application/json':
        return unsupported_media_type()
    try:
        content = request.get_json()
        if 'username' not in content or 'password' not in content:
            return invalid_credentials()
        if 'clientToken' not in content:
            content['clientToken'] = str(uuid.uuid4())
        if not validate_user(content['username'],content['password']):
            return invalid_credentials()
        c.execute("DELETE FROM users WHERE username=?", (content['username'],))
        accessToken = str(uuid.uuid4())
        c.execute("INSERT INTO users (username, clientToken, accessToken) VALUES (?,?,?)", (content['username'],content['clientToken'],accessToken))
        conn.commit()
        response = {"accessToken":accessToken,"clientToken":content['clientToken']}
        return json.dumps(response)



    except Exception as e:
        return custom_exception({"error":str(type(e).__name__), "errorMessage":str(e)})


@app.errorhandler(404)
def errornotfound(e):
    args = {"error":"Not Found","errorMessage":"The server has not found anything matching the request URI"}
    return json.dumps(args), 404

app.debug = True
app.run(host="0.0.0.0", port=5000)
