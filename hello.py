
from flask import Flask
app = Flask(__name__)

@app.route("/index")
def index():
    return '<h1>Hello Test Flask Yo</h1>'
