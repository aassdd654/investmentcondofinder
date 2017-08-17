
from flask import Flask
app = Flask(__name__)

@app.route("/")
def index():
    return '<h1>index page</h1>'

@app.route("/hello")
def hello():
    return '<h1>hello page: Test Flask Yo</h1>'

if __name__ == '__main__':
    app.run(debug=True)
