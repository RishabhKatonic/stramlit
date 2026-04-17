# Katonic Job Test Scripts

Seven ready-to-deploy scripts — one per Job template in Studio > Jobs.

```
job-scripts-fixed/
├── batch-prediction/            → predict.py          (inference over CSV)
├── data-processing-pipeline/    → pipeline.py         (ETL: clean, dedupe, rename, dates)
├── data-quality-check/          → validate.py         (null / schema / dupe / range checks)
├── hyperparameter-tuning/       → tune.py             (GridSearchCV)
├── knowledge-connector/         → sync.py             (chunk docs for ingestion)
├── ml-model-training/           → train.py            (sklearn classifier / regressor)
└── scheduled-report/            → generate_report.py  (csv / json / html / pdf)
```

Each folder has:
- a Python script
- `requirements.txt` (empty placeholder where no deps are needed, so `pip install -r` still succeeds)
- sample input / schema / rules files where relevant

---

## One-time setup

1. **Push this folder to a GitHub repo** — suggest naming it `job-scripts-fixed` so the paths in the commands match.
2. **Open Studio → Storage → New Dataset** and create a dataset called **`job-test-data`** (or keep the name you already have — e.g. `workk`).
3. **Upload sample inputs** into that dataset:
   - `sample_input.csv` — used by Data Processing + Data Quality + Scheduled Report
   - `sample_train.csv` → rename to `train.csv` — used by ML Training + Hyperparameter Tuning
   - A few `.txt` / `.md` / `.html` files — used by Knowledge Connector

Upload everything at the **root** of the dataset (not inside a subfolder) so the pod sees them directly at `/data/<file>.csv`.

---

## How Storage works in Jobs

The Create Job form has **three independent fields** (per the new UI):

| Field | What it does | Mount path inside pod |
|---|---|---|
| **Code Source** = GitHub | Clones your repo into `/app/repo/` | Commands run from `/app/repo/` |
| **Input Dataset** | Mounts a Storage dataset read/write | `/data/` |
| **Output Dataset** | Mounts a Storage dataset for writes that should show up in Storage UI | `/reports/` and `/outputs/` |

So a typical workflow:
```
Code Source:     GitHub  →  job-scripts-fixed repo  →  /app/repo/job-scripts-fixed/...
Input Dataset:   job-test-data  →  /data/sample_input.csv
Output Dataset:  job-test-data  →  /reports/...  and  /outputs/...
```

Files written to `/reports/` or `/outputs/` **persist back to Storage UI** under `<dataset>/reports/...` and `<dataset>/outputs/...`.
Files written to `/tmp/` or anywhere else are **lost** when the pod exits.

---

## Common recipe for every job

Fill these the same way for all 7 jobs:

| Field | Value |
|---|---|
| **Container Image** | Per-job (see tables below). Default: `python:3.12-slim` |
| **Code Source** | `GitHub` |
| **Git Username** | your GitHub username |
| **Git Token** | empty for public repos |
| **Repository** | name of the repo you pushed `job-scripts-fixed-fixed` to |
| **Branch** | `main` |
| **Input Dataset** | `job-test-data` |
| **Output Dataset** | `job-test-data` |
| **Resources** | `small` (CPU) — bump to `medium` for training/tuning if needed |

Suggested run order: **ML Training first** (produces `model.pkl`), then **Batch Prediction** (uses it). Everything else is independent.

---

## Per-job commands

### 1. Data Processing Pipeline

| Field | Value |
|---|---|
| **Image** | `python:3.12-slim` |
| **Command** | `python job-scripts-fixed/data-processing-pipeline/pipeline.py --input /data --output /reports/processed --trim --dedupe --required-columns id,email --date-fields signup_date` |
| **Expect** | Logs show `5 → 3 rows`; `reports/processed/sample_input.csv` appears in Storage |

### 2. Data Quality Check

| Field | Value |
|---|---|
| **Image** | `python:3.12-slim` |
| **Command** | `python job-scripts-fixed/data-quality-check/validate.py --input /data --output /reports/dq --schema /app/repo/job-scripts-fixed/data-quality-check/schema.json --rules /app/repo/job-scripts-fixed/data-quality-check/rules.json` |
| **Expect** | `reports/dq/report.json` with pass/fail counts; exits 1 if any FAIL, 0 otherwise |

Note: `--schema` and `--rules` use `/app/repo/...` because those config files live in the cloned repo, not in the input dataset.

### 3. Scheduled Report (CronJob)

| Field | Value |
|---|---|
| **Image** | `python:3.12-slim` |
| **Command** | `pip install -r job-scripts-fixed/scheduled-report/requirements.txt --quiet && python job-scripts-fixed/scheduled-report/generate_report.py --input /data --output /reports --format csv --title "Daily Metrics"` |
| **Schedule** | `0 9 * * *` (9am UTC daily) |
| **Expect** | A new `reports/report_YYYYMMDD_HHMMSS.csv` per run |

For PDF output use `--format pdf` (the pip install brings in `reportlab`).

### 4. ML Model Training

| Field | Value |
|---|---|
| **Image** | `python:3.12-slim` |
| **Command** | `pip install -r job-scripts-fixed/ml-model-training/requirements.txt --quiet && python job-scripts-fixed/ml-model-training/train.py --input /data/train.csv --output /reports/model.pkl --label-col target --model rf` |
| **Prerequisite** | Upload `sample_train.csv` to the dataset as `train.csv` |
| **Expect** | `reports/model.pkl` + `reports/model_meta.json` (accuracy / f1 / feature names) |

Swap `--model rf` for `lr` (linear) or `gbm` (gradient boosting) to try different algorithms.

### 5. Batch Prediction

| Field | Value |
|---|---|
| **Image** | `python:3.12-slim` |
| **Command** | `pip install -r job-scripts-fixed/batch-prediction/requirements.txt --quiet && python job-scripts-fixed/batch-prediction/predict.py --model /data/reports/model.pkl --input /data/train.csv --output /reports/predictions.csv` |
| **Prerequisite** | Run job #4 first — its `model.pkl` ends up at `/data/reports/model.pkl` on the next run |
| **Expect** | `reports/predictions.csv` with original columns + a `prediction` column; plus `predictions_meta.json` |

### 6. Hyperparameter Tuning

| Field | Value |
|---|---|
| **Image** | `python:3.12-slim` |
| **Command** | `pip install -r job-scripts-fixed/hyperparameter-tuning/requirements.txt --quiet && python job-scripts-fixed/hyperparameter-tuning/tune.py --input /data/train.csv --output /reports --label-col target --trials 12 --cv 3` |
| **Expect** | `reports/best_model.pkl`, `reports/best_params.json`, `reports/metrics.json` |
| **Resources** | `medium` recommended — CV on small CPU is slow |

### 7. Knowledge Connector

| Field | Value |
|---|---|
| **Image** | `quay.io/katonic/connectorsdk:connector-sdk-v3-python-3.11` |
| **Command** | `python job-scripts-fixed/knowledge-connector/sync.py --source /data --output /reports/chunks.json --chunk-size 500 --overlap 50` |
| **Prerequisite** | Upload `.txt` / `.md` / `.html` / `.rst` files to the dataset |
| **Expect** | `reports/chunks.json` containing chunked text with source refs + `meta` block |

---

## Verifying success

Open the job's detail page:

- **Overview tab** → `Completed` status, pods = 1-1, duration shown
- **Run History tab** → one entry with `startedAt`, `duration`, `exitCode` = 0
- **Logs tab** → `[INFO]` lines showing what the script read and wrote
- **Storage UI** (open the output dataset) → output files under `reports/...` or `outputs/...`

Note: once the Job finishes, the K8s pod is automatically cleaned up from the cluster — but the UI keeps showing everything (Overview, Run History, Logs) because MDS persists the status + log tail to the DB. The Logs tab works even after the pod is gone.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `Input directory not found: /data/...` | Didn't select **Input Dataset** in the form | Edit job → set Input Dataset → Update & Redeploy |
| `0 CSV, 0 JSON` logged but files exist in Storage | Files are inside a subfolder; script looked at dataset root | Either move files to the root, or change `--input` to match (e.g. `--input /data/myfolder`) |
| Job Completed but nothing in Storage → `reports/` | No **Output Dataset** selected, or script wrote to `/tmp/` | Set Output Dataset AND write to `/reports/` or `/outputs/` |
| `ModuleNotFoundError` | `requirements.txt` wasn't installed | Prepend `pip install -r job-scripts-fixed/<task>/requirements.txt --quiet &&` to the Command |
| `Permission denied: /reports/...` | Output Dataset missing | Select one in the form |
| Logs tab empty while pod is gone | Pod was auto-cleaned before MDS captured logs | Hit Refresh a few seconds after Completed status; log tail is pulled on the next status sync |

---

## Changes from v1 (tracking what improved)

| Script | Key fix |
|---|---|
| `pipeline.py` | Adds `--trim --dedupe --required-columns --rename --date-fields` flags; preserves subdir structure in output; per-file error handling; exits non-zero if any file fails |
| `validate.py` | Removes fake sample-data fallback; reads external `schema.json`; auto-detects key column for dupes; range rules via `rules.json` |
| `generate_report.py` | Reads REAL data from `--input` (no more hardcoded placeholder metrics); honest PDF fallback to HTML if reportlab missing; defaults to `/reports` (persistent) |
| `predict.py` | New — batch inference with cloudpickle fallback for custom model classes |
| `train.py` | New — sklearn trainer, auto-detects classification vs regression, multiple algorithm choices |
| `tune.py` | New — GridSearchCV with configurable trial count + CV folds |
| `sync.py` | Cleaner HTML stripping, word-aware chunking with overlap, max-chunks safety cap |
