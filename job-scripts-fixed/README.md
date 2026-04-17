# Katonic Job Test Scripts (Fixed)

Seven ready-to-deploy scripts, one per Job template.

```
job-scripts-fixed/
├── batch-prediction/            → predict.py       (inference over CSV)
├── data-processing-pipeline/    → pipeline.py      (ETL: clean, dedupe, rename, dates)
├── data-quality-check/          → validate.py      (null/schema/dupe/range checks)
├── hyperparameter-tuning/       → tune.py          (GridSearchCV)
├── knowledge-connector/         → sync.py          (chunk docs for ingestion)
├── ml-model-training/           → train.py         (sklearn classifier/regressor)
└── scheduled-report/            → generate_report.py (csv/json/html/pdf)
```

Each folder has:
- a script (`*.py`)
- `requirements.txt` (even if empty, so `pip install -r` succeeds)
- optional sample input data

---

## Setup (one-time)

1. **Push this folder to GitHub** — as `deploy-model/` or `job-scripts/` in your test repo.
2. **Create a Storage dataset** called `job-test-data` in Storage UI.
3. **Upload sample data** — the CSV files in each script folder, or your own.

---

## Per-job test plan

### 1. Data Processing Pipeline

| Field | Value |
|---|---|
| **Image** | `python:3.12-slim` |
| **Command** | `pip install -r job-scripts/data-processing-pipeline/requirements.txt && python job-scripts/data-processing-pipeline/pipeline.py --input /data --output /reports/processed --trim --dedupe --required-columns id,email` |
| **Input Dataset** | `job-test-data` (upload `sample_input.csv`) |
| **Output Dataset** | `job-test-data` (same) |
| **Source** | GitHub |
| **Expect** | Logs show "5 → 3 rows", `reports/processed/sample_input.csv` appears in Storage |

### 2. Data Quality Check

| Field | Value |
|---|---|
| **Command** | `python job-scripts/data-quality-check/validate.py --input /data --output /reports/dq --schema /app/repo/job-scripts/data-quality-check/schema.json --rules /app/repo/job-scripts/data-quality-check/rules.json` |
| **Input Dataset** | `job-test-data` |
| **Output Dataset** | `job-test-data` |
| **Expect** | `reports/dq/report.json` with pass/fail counts; job exits 1 if any FAIL, 0 otherwise |

### 3. Scheduled Report (CronJob)

| Field | Value |
|---|---|
| **Command** | `pip install -r job-scripts/scheduled-report/requirements.txt && python job-scripts/scheduled-report/generate_report.py --input /data --output /reports --format csv --title "Daily Metrics"` |
| **Schedule** | `0 9 * * *` (every day at 9am UTC) |
| **Input Dataset** | `job-test-data` |
| **Output Dataset** | `job-test-data` |
| **Expect** | `reports/report_YYYYMMDD_HHMMSS.csv` appears per run |

### 4. Batch Prediction

| Field | Value |
|---|---|
| **Command** | `pip install -r job-scripts/batch-prediction/requirements.txt && python job-scripts/batch-prediction/predict.py --model /data/model.pkl --input /data/inputs.csv --output /reports/predictions.csv` |
| **Prerequisite** | Upload a trained `model.pkl` (from job #5) and `inputs.csv` to the dataset |
| **Expect** | `reports/predictions.csv` with original columns + `prediction` column, plus `predictions_meta.json` |

### 5. ML Model Training

| Field | Value |
|---|---|
| **Command** | `pip install -r job-scripts/ml-model-training/requirements.txt && python job-scripts/ml-model-training/train.py --input /data/train.csv --output /reports/model.pkl --label-col target --model rf` |
| **Input** | Upload `sample_train.csv` as `train.csv` |
| **Output Dataset** | `job-test-data` |
| **Expect** | `reports/model.pkl` + `reports/model_meta.json` with accuracy/f1 metrics |

### 6. Hyperparameter Tuning

| Field | Value |
|---|---|
| **Command** | `pip install -r job-scripts/hyperparameter-tuning/requirements.txt && python job-scripts/hyperparameter-tuning/tune.py --input /data/train.csv --output /reports --label-col target --trials 12 --cv 3` |
| **Input** | Same `train.csv` from job #5 |
| **Expect** | `reports/best_model.pkl`, `reports/best_params.json`, `reports/metrics.json` |

### 7. Knowledge Connector

| Field | Value |
|---|---|
| **Image** | `quay.io/katonic/connectorsdk:connector-sdk-v3-python-3.11` |
| **Command** | `python job-scripts/knowledge-connector/sync.py --source /data --output /reports/chunks.json --chunk-size 500 --overlap 50` |
| **Input** | Upload `.txt` / `.md` / `.html` files to the dataset |
| **Expect** | `reports/chunks.json` with chunked text + source file references |

---

## Common recipe for every job

1. **Source**: GitHub
2. **Git Username**: your username
3. **Git Token**: optional for public repos
4. **Repo Name**: where you pushed this folder
5. **Branch**: `main`
6. **Input Dataset**: `job-test-data`
7. **Output Dataset**: `job-test-data` (so output lands in Storage UI)

---

## Verifying success

- **Run History tab** → run status = `completed`, duration in seconds, exit code 0
- **Logs tab** → each script prints `[INFO]` lines showing what it did
- **Storage UI** → output files appear under `<dataset>/reports/...` after the job finishes
- If `completed` but no output files → the command wrote to `/tmp/` (ephemeral) instead of `/reports/` or `/outputs/`

---

## Changes from v1

| Script | Key fix |
|---|---|
| `pipeline.py` | Adds `--trim --dedupe --required-columns --rename --date-fields` CLI flags; preserves subdir structure; per-file error handling |
| `validate.py` | Removes fake sample-data fallback; schema check reads external `schema.json`; auto-detects key column for dupes; configurable range rules |
| `generate_report.py` | Reads REAL data from `--input` (no more hardcoded placeholder); honest PDF fallback to HTML if reportlab missing; defaults to `/reports` (persistent) |
| `predict.py` | New — batch inference with cloudpickle fallback for custom classes |
| `train.py` | New — sklearn trainer, auto-detects classification vs regression |
| `tune.py` | New — GridSearchCV with configurable trial count |
| `sync.py` | Cleaner HTML handling, paragraph/word-aware chunking, max-chunks safety cap |
