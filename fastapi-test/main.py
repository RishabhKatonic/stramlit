"""
Katonic App Deployment — FastAPI Test App
Framework: FastAPI | Port: 8000
Run: uvicorn main:app --host 0.0.0.0 --port 8000
"""
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import datetime
import os

app = FastAPI(title="Katonic FastAPI Test", version="1.0.0")


@app.get("/", response_class=HTMLResponse)
def root():
    return f"""
    <!DOCTYPE html>
    <html>
    <head><title>Katonic FastAPI Test</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; }}
        .success {{ color: green; font-size: 18px; }}
        .info {{ background: #f0f0f0; padding: 15px; border-radius: 8px; margin: 10px 0; }}
        h1 {{ color: #2c3e50; }}
        a {{ color: #3498db; }}
    </style>
    </head>
    <body>
        <h1>🚀 Katonic FastAPI Test App</h1>
        <p class="success">✅ FastAPI is running successfully on Katonic!</p>
        <div class="info">
            <h3>📋 Environment Info</h3>
            <ul>
                <li><b>Framework:</b> FastAPI</li>
                <li><b>Port:</b> 8000</li>
                <li><b>Hostname:</b> {os.getenv("HOSTNAME", "unknown")}</li>
                <li><b>Timestamp:</b> {datetime.datetime.now().isoformat()}</li>
            </ul>
        </div>
        <h3>🧪 Test Endpoints</h3>
        <ul>
            <li><a href="/health">/health</a> — Health check</li>
            <li><a href="/info">/info</a> — System info (JSON)</li>
            <li><a href="/greet/KatonicUser">/greet/{{name}}</a> — Greeting API</li>
            <li><a href="/compute?a=10&b=5&op=add">/compute?a=10&b=5&op=add</a> — Calculator API</li>
            <li><a href="/docs">/docs</a> — Swagger UI (auto-generated)</li>
        </ul>
        <hr>
        <p style="color:gray;">Katonic App Deployment Test | {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </body>
    </html>
    """


@app.get("/health")
def health():
    return {"status": "healthy", "framework": "FastAPI", "timestamp": datetime.datetime.now().isoformat()}


@app.get("/info")
def info():
    return {
        "framework": "FastAPI",
        "port": 8000,
        "hostname": os.getenv("HOSTNAME", "unknown"),
        "python_version": os.popen("python --version").read().strip(),
        "timestamp": datetime.datetime.now().isoformat(),
    }


@app.get("/greet/{name}")
def greet(name: str):
    return {"message": f"Hello, {name}! Your FastAPI app is working! 🎉"}


@app.get("/compute")
def compute(a: float = 10, b: float = 5, op: str = "add"):
    operations = {
        "add": a + b,
        "subtract": a - b,
        "multiply": a * b,
        "divide": a / b if b != 0 else "Error: Division by zero",
    }
    result = operations.get(op, "Unknown operation")
    return {"a": a, "b": b, "operation": op, "result": result}
