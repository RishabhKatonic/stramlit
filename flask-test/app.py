"""
Katonic App Deployment — Flask Test App
Framework: Flask | Port: 5000
Run: flask run --host 0.0.0.0 --port 5000
"""
from flask import Flask, jsonify, request
import datetime
import os

app = Flask(__name__)


@app.route("/")
def root():
    return f"""
    <!DOCTYPE html>
    <html>
    <head><title>Katonic Flask Test</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; }}
        .success {{ color: green; font-size: 18px; }}
        .info {{ background: #f0f0f0; padding: 15px; border-radius: 8px; margin: 10px 0; }}
        h1 {{ color: #2c3e50; }}
        a {{ color: #3498db; }}
    </style>
    </head>
    <body>
        <h1>🚀 Katonic Flask Test App</h1>
        <p class="success">✅ Flask is running successfully on Katonic!</p>
        <div class="info">
            <h3>📋 Environment Info</h3>
            <ul>
                <li><b>Framework:</b> Flask</li>
                <li><b>Port:</b> 5000</li>
                <li><b>Hostname:</b> {os.getenv("HOSTNAME", "unknown")}</li>
                <li><b>Timestamp:</b> {datetime.datetime.now().isoformat()}</li>
            </ul>
        </div>
        <h3>🧪 Test Endpoints</h3>
        <ul>
            <li><a href="/health">/health</a> — Health check</li>
            <li><a href="/info">/info</a> — System info (JSON)</li>
            <li><a href="/greet?name=KatonicUser">/greet?name=KatonicUser</a> — Greeting API</li>
            <li><a href="/echo">/echo</a> — POST echo endpoint</li>
        </ul>
        <hr>
        <p style="color:gray;">Katonic App Deployment Test | {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </body>
    </html>
    """


@app.route("/health")
def health():
    return jsonify(status="healthy", framework="Flask", timestamp=datetime.datetime.now().isoformat())


@app.route("/info")
def info():
    return jsonify(
        framework="Flask",
        port=5000,
        hostname=os.getenv("HOSTNAME", "unknown"),
        timestamp=datetime.datetime.now().isoformat(),
    )


@app.route("/greet")
def greet():
    name = request.args.get("name", "World")
    return jsonify(message=f"Hello, {name}! Your Flask app is working! 🎉")


@app.route("/echo", methods=["POST"])
def echo():
    data = request.get_json(silent=True) or {}
    return jsonify(received=data, timestamp=datetime.datetime.now().isoformat())


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
