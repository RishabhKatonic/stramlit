/**
 * Katonic App Deployment — Node/React Test App
 * Framework: Node/React | Port: 3000
 * Run: npm start (-> node server.js)
 */
const express = require("express");
const os = require("os");

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());

// Health check
app.get("/health", (req, res) => {
  res.json({
    status: "healthy",
    framework: "Node/React",
    timestamp: new Date().toISOString(),
  });
});

// API info
app.get("/api/info", (req, res) => {
  res.json({
    framework: "Node/React (Express)",
    port: PORT,
    hostname: os.hostname(),
    nodeVersion: process.version,
    uptime: Math.floor(process.uptime()) + "s",
    timestamp: new Date().toISOString(),
  });
});

// Greet API
app.get("/api/greet/:name", (req, res) => {
  res.json({ message: `Hello, ${req.params.name}! Your Node/React app is working! 🎉` });
});

// Serve React SPA (inline — no build step needed)
app.get("/", (req, res) => {
  res.send(`<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Katonic Node/React Test</title>
  <script src="https://unpkg.com/react@18/umd/react.production.min.js" crossorigin></script>
  <script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js" crossorigin></script>
  <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
  <style>
    body { font-family: Arial, sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; background: #fafafa; }
    .success { color: green; font-size: 18px; }
    .info { background: #fff; padding: 15px; border-radius: 8px; margin: 10px 0; border: 1px solid #ddd; }
    .btn { padding: 8px 16px; background: #3498db; color: white; border: none; border-radius: 4px; cursor: pointer; margin: 5px; }
    .btn:hover { background: #2980b9; }
    pre { background: #2c3e50; color: #ecf0f1; padding: 12px; border-radius: 6px; overflow-x: auto; }
    h1 { color: #2c3e50; }
  </style>
</head>
<body>
  <div id="root"></div>
  <script type="text/babel">
    function App() {
      const [info, setInfo] = React.useState(null);
      const [greeting, setGreeting] = React.useState("");
      const [name, setName] = React.useState("Katonic User");

      React.useEffect(() => {
        fetch("/api/info").then(r => r.json()).then(setInfo);
      }, []);

      const fetchGreeting = () => {
        fetch("/api/greet/" + encodeURIComponent(name))
          .then(r => r.json())
          .then(data => setGreeting(data.message));
      };

      return (
        <div>
          <h1>🚀 Katonic Node/React Test App</h1>
          <p className="success">✅ Node/React is running successfully on Katonic!</p>

          <div className="info">
            <h3>📋 Environment Info</h3>
            {info ? <pre>{JSON.stringify(info, null, 2)}</pre> : <p>Loading...</p>}
          </div>

          <div className="info">
            <h3>🧪 Interactive Test</h3>
            <input
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder="Your name"
              style={{ padding: "8px", marginRight: "10px", borderRadius: "4px", border: "1px solid #ccc" }}
            />
            <button className="btn" onClick={fetchGreeting}>Say Hello</button>
            {greeting && <p style={{ fontSize: "18px" }}>{greeting}</p>}
          </div>

          <hr />
          <p style={{ color: "gray" }}>Katonic App Deployment Test | Node/React</p>
        </div>
      );
    }
    ReactDOM.createRoot(document.getElementById("root")).render(<App />);
  </script>
</body>
</html>`);
});

app.listen(PORT, "0.0.0.0", () => {
  console.log(`✅ Katonic Node/React Test App running on http://0.0.0.0:${PORT}`);
});
