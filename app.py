from flask import Flask, request, render_template, send_file
import json
app = Flask(__name__)

################## Errors ##################
def method_not_allowed():
    args = {"error":"Method Not Allowed","errorMessage":"The method specified in the request is not allowed for the resource identified by the request URI"}
    return json.dumps(args)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return send_file("index.html")
    if request.method == 'POST':
        return method_not_allowed()

@app.errorhandler(404)
def errornotfound(e):
    args = {"error":"Not Found","errorMessage":"The server has not found anything matching the request URI"}
    return json.dumps(args)

app.debug = True
app.run(host="0.0.0.0", port=5000)
