from flask import Flask
import os
import socket

app = Flask(__name__)

@app.route('/')
def hello():
    # Displays where the application is running
    hostname = socket.gethostname()
    return f"<h1>Hello from the Aether App!</h1><p>Running on node: <b>{hostname}</b></p>"

@app.route('/load')
def load():
    # This endpoint simulates a heavy computational load
    for i in range(100000000):
        _ = i * i
    return "CPU load simulation complete!"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
