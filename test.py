from flask import Flask
from flask import render_template

LOCKED_PORT = 5555

app = Flask(__name__)

@app.route("/")
def root_page():
    return "hello test"
