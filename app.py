from flask import Flask, request, render_template, send_file
app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return send_file("index.html")
    if request.method == 'POST':
        content = request.json
        
app.debug = True
app.run(host="0.0.0.0", port=5000)
