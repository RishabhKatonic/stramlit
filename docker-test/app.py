"""
Katonic App Deployment — Docker Test App
Framework: Docker (custom container) | Port: 8080
Run: docker build -t katonic-docker-test . && docker run -p 8080:8080 katonic-docker-test
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import datetime
import os


class KatonicHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self._json_response({
                "status": "healthy",
                "framework": "Docker (custom)",
                "timestamp": datetime.datetime.now().isoformat(),
            })
        elif self.path == "/info":
            self._json_response({
                "framework": "Docker (custom container)",
                "port": 8080,
                "hostname": os.getenv("HOSTNAME", "unknown"),
                "python_version": os.popen("python --version").read().strip(),
                "timestamp": datetime.datetime.now().isoformat(),
            })
        else:
            self._html_response()

    def _json_response(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())

    def _html_response(self):
        html = f"""<!DOCTYPE html>
<html>
<head><title>Katonic Docker Test</title>
<style>
    body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; }}
    .success {{ color: green; font-size: 18px; }}
    .info {{ background: #f0f0f0; padding: 15px; border-radius: 8px; margin: 10px 0; }}
    h1 {{ color: #2c3e50; }}
    a {{ color: #3498db; }}
</style>
</head>
<body>
    <h1>🚀 Katonic Docker Test App</h1>
    <p class="success">✅ Docker container is running successfully on Katonic!</p>
    <div class="info">
        <h3>📋 Environment Info</h3>
        <ul>
            <li><b>Framework:</b> Docker (custom container)</li>
            <li><b>Port:</b> 8080</li>
            <li><b>Hostname:</b> {os.getenv("HOSTNAME", "unknown")}</li>
            <li><b>Base Image:</b> python:3.12-slim</li>
            <li><b>Timestamp:</b> {datetime.datetime.now().isoformat()}</li>
        </ul>
    </div>
    <h3>🧪 Test Endpoints</h3>
    <ul>
        <li><a href="/health">/health</a> — Health check (JSON)</li>
        <li><a href="/info">/info</a> — System info (JSON)</li>
    </ul>
    <hr>
    <p style="color:gray;">Katonic App Deployment Test | Docker | {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
</body>
</html>"""
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode())

    def log_message(self, format, *args):
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {args[0]}", flush=True)


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 8080), KatonicHandler)
    print("✅ Katonic Docker Test App running on http://0.0.0.0:8080", flush=True)
    server.serve_forever()
