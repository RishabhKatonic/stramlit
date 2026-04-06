# Katonic App Deployment — Test Apps

Test applications for all 7 frameworks supported by Katonic 7.0 App Deployment.

## Quick Reference

| Framework   | Port | Entry File   | Run Command                                      | Install Command              |
|-------------|------|-------------|--------------------------------------------------|------------------------------|
| Streamlit   | 8501 | `app.py`    | `streamlit run app.py --server.port=8501`        | `pip install -r requirements.txt` |
| Dash        | 8050 | `app.py`    | `python app.py`                                  | `pip install -r requirements.txt` |
| Gradio      | 7860 | `app.py`    | `python app.py`                                  | `pip install -r requirements.txt` |
| FastAPI     | 8000 | `main.py`   | `uvicorn main:app --host 0.0.0.0 --port 8000`   | `pip install -r requirements.txt` |
| Flask       | 5000 | `app.py`    | `flask run --host 0.0.0.0 --port 5000`          | `pip install -r requirements.txt` |
| Node/React  | 3000 | `server.js` | `npm start`                                      | `npm install`                |
| Docker      | 8080 | `app.py`    | Custom (from Dockerfile)                         | `docker build`               |

## Repo Structure

```
katonic-app-test/
├── README.md
├── streamlit-test/
│   ├── app.py
│   └── requirements.txt
├── dash-test/
│   ├── app.py
│   └── requirements.txt
├── gradio-test/
│   ├── app.py
│   └── requirements.txt
├── fastapi-test/
│   ├── main.py              ← must be main.py (uvicorn main:app)
│   └── requirements.txt
├── flask-test/
│   ├── app.py
│   └── requirements.txt
├── node-react-test/
│   ├── server.js
│   └── package.json
└── docker-test/
    ├── Dockerfile
    ├── app.py
    └── requirements.txt
```

## How to Deploy on Katonic

1. Push this repo (or individual folders) to a GitHub repo
2. Go to **Katonic Platform → App Deployment → Deploy App**
3. Select the framework
4. Provide the Git repo URL and branch
5. Set the **script path** to the subfolder (e.g., `streamlit-test/app.py`)
6. Allocate resources and deploy

## What Each Test App Validates

Every app covers:
- **Startup** — App starts and binds to the correct port
- **Health check** — `/health` endpoint returns JSON status
- **Environment** — Displays hostname, timestamp, framework info
- **Interactivity** — At least one interactive feature (form, chart, API)
- **Correct port** — Matches Katonic's expected framework port

## Notes

- **FastAPI**: The file **must** be `main.py` because Katonic runs `uvicorn main:app`
- **Flask**: Katonic uses `flask run`, which auto-discovers `app.py` via the `app` object
- **Node/React**: Uses Express + inline React (CDN) — no build step needed
- **Docker**: Uses pure Python stdlib (`http.server`) — zero external dependencies
- **Gradio**: Uses `gr.Blocks` with tabbed interface for comprehensive testing
