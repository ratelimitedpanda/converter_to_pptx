import os
import sys
import tempfile
import uuid

from flask import Flask, render_template, request, send_file
sys.stdout.reconfigure(encoding="utf-8")


app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")



if __name__ == "__main__":
    app.run(debug=True)
