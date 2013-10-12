from flask import Flask, request, render_template, send_file
import json
app = Flask(__name__)

################## Errors ##################
def method_not_allowed():
    args = {"error":"Method Not Allowed","errorMessage":"The method specified in the request is not allowed for the resource identified by the request URI"}
    return json.dumps(args)

def invalid_credentials_migrated():
    args = {"error":"ForbiddenOperationException","errorMessage":"Invalid credentials. Account migrated, use e-mail as username.","cause":"UserMigratedException"}
    return json.dumps(args)

def invalid_credentials():
    args = {"error":"ForbiddenOperationException","errorMessage":"Invalid credentials. Invalid username or password."}
    return json.dumps(args)

def invalid_token():
    args = {"error":"ForbiddenOperationException","errorMessage":"Invalid token."}
    return json.dumps(args)

def illegal_argument_exception():
    args = {"error":"IllegalArgumentException","errorMessage":"Access token already has a profile assigned."}
    return json.dumps(args)

def unsupported_media_type():
    args = {"error":"Unsupported Media Type","errorMessage":"The server is refusing to service the request because the entity of the request is in a format not supported by the requested resource for the requested method"}
    return json.dumps(args)

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
    json = request.get_json()

@app.errorhandler(404)
def errornotfound(e):
    args = {"error":"Not Found","errorMessage":"The server has not found anything matching the request URI"}
    return json.dumps(args)

app.debug = True
app.run(host="0.0.0.0", port=5000)
