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
); 

CREATE TABLE verify(
ID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
username TEXT NOT NULL,
serverId TEXT NOT NULL
);"""

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
    import pexpect
    import re
    username = re.findall(r"[a-z0-9]+",username)[0]
    p = pexpect.spawn('/usr/bin/kinit --cache=/dev/null %s@%s' % (username, "LOCAL.TJHSST.EDU"))
    p.expect(".*Password: ")
    p.sendline(password)
    e = p.expect([pexpect.EOF,"kinit: .*"])
    return not(e)
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
    if not(request.mimetype == 'application/json' or request.mimetype == 'application/x-www-form-urlencoded'):
        return unsupported_media_type()
    try:
        content = request.get_json()
        if not content:
            content = request.form
        if 'username' not in content or 'password' not in content:
            return invalid_credentials()
        if 'clientToken' not in content:
            content['clientToken'] = str(uuid.uuid4())
            c.execute("DELETE FROM users WHERE username=?", (content['username'],))
        if not validate_user(content['username'],content['password']):
            return invalid_credentials()
        accessToken = str(uuid.uuid4())
        profileId = uuid.uuid4().hex
        c.execute("INSERT INTO users (username, clientToken, accessToken) VALUES (?,?,?)", (content['username'],content['clientToken'],accessToken))
        conn.commit()
        response = {"accessToken":accessToken,"clientToken":content['clientToken'],"availableProfiles":[{"id":profileId,"name":content['username']}],"selectedProfile":{"id":profileId,"name":content['username']}}
        return json.dumps(response)
    except Exception as e:
        return custom_exception({"error":str(type(e).__name__), "errorMessage":str(e)})

@app.route('/refresh', methods=['GET', 'POST'])
def refresh():
    if request.method == 'GET':
        return method_not_allowed()
    if not(request.mimetype == 'application/json' or request.mimetype == 'application/x-www-form-urlencoded'):
        return unsupported_media_type()
    try:
        content = request.get_json()
        if not content:
            content = request.form
        if 'accessToken' not in content or 'clientToken' not in content:
            return invalid_token()
        c.execute("SELECT * FROM users WHERE clientToken=? AND accessToken=?", (content['clientToken'],content['accessToken']))
        u = c.fetchone()
        if not u:
            return invalid_token()
        client = u[3]
        userid = u[0] 
        access = str(uuid.uuid4())
        c.execute("UPDATE users SET accessToken='%s' WHERE ID=?" % access, (userid,))
        conn.commit()
        response = {"accessToken":access,"clientToken":client}
        return json.dumps(response)
    except Exception as e:
        return custom_exception({"error":str(type(e).__name__), "errorMessage":str(e)})

@app.route('/validate', methods=['GET', 'POST'])
def validate():
    if request.method == 'GET':
        return method_not_allowed()
    if not(request.mimetype == 'application/json' or request.mimetype == 'application/x-www-form-urlencoded'):
        return unsupported_media_type()
    try:
        content = request.get_json()
        if not content:
            content = request.form
        if 'accessToken' not in content:
            return invalid_token()
        c.execute("SELECT * FROM users WHERE accessToken=?", (content['accessToken'],))
        u = c.fetchone()
        if not u:
            return invalid_token()
        return ""
    except Exception as e:
        return custom_exception({"error":str(type(e).__name__), "errorMessage":str(e)})

@app.route('/game/joinserver')
@app.route('/game/joinserver.jsp')
def joinserver():
    content = request.args
    if 'user' not in content or 'sessionId' not in content or 'serverId' not in content:
        return ""
    sessionId = content['sessionId'].split(":")
    if len(sessionId) != 3:
        return ""
    accessToken = sessionId[1]
    c.execute("SELECT * FROM users WHERE accessToken=?", (accessToken,))
    u = c.fetchone()
    if not u:
        return ""
    if u[1] != content['user']:
        return ""
    c.execute("DELETE FROM verify WHERE serverId=? AND username=?", (content['serverId'], content['user']))
    c.execute("INSERT INTO verify (username, serverId) VALUES (?,?)", (content['user'], content['serverId']))
    conn.commit()
    return "OK"

@app.route('/game/checkserver')
@app.route('/game/checkserver.jsp')
def checkserver():
    content = request.args
    if 'user' not in content or 'serverId' not in content:
        return ""
    c.execute("SELECT * FROM verify WHERE serverId=? AND username=?", (content['serverId'], content['user']))
    u = c.fetchone()
    if not u:
        return ""
    c.execute("DELETE FROM verify WHERE serverId=? AND username=?", (content['serverId'], content['user']))
    conn.commit()
    return "YES"

@app.errorhandler(404)
def errornotfound(e):
    args = {"error":"Not Found","errorMessage":"The server has not found anything matching the request URI"}
    return json.dumps(args), 404

app.debug = False
app.run(host="0.0.0.0", port=5000)
