# Katonic Job Templates — Test Suite

Unit tests for all job templates available in the Katonic Platform **Create Job** wizard.

## Job Templates Covered

| # | Template                  | Script Under Test       | Container Image                            | Command                                                        |
|---|---------------------------|-------------------------|--------------------------------------------|----------------------------------------------------------------|
| 1 | **Scheduled Report**      | `generate_report.py`    | `python:3.12-slim`                         | `python generate_report.py --format pdf`                       |
| 2 | **Batch Prediction**      | `predict.py`            | `python:3.11-slim`                         | `python predict.py --model /models/latest --batch-size 256`    |
| 3 | **Data Processing Pipeline** | `pipeline.py`        | `python:3.12-slim`                         | `python pipeline.py --input /data/raw --output /data/processed`|
| 4 | **Data Quality Check**    | `validate.py`           | `python:3.12-slim`                         | `python validate.py --suite full --output /reports/dq`         |
| 5 | **Knowledge Connector**   | `sync.py`               | `connectorsdk:connector-sdk-v2-python-3.11`| `python sync.py`                                               |
| 6 | **ML Model Training**     | (user-defined)          | GPU-enabled image                          | (user-defined)                                                 |
| 7 | **Hyperparameter Tuning** | (user-defined)          | GPU-enabled image                          | (user-defined)                                                 |

## Running Tests

```bash
# Run all tests
python -m pytest job-tests/ -v

# Run a single job's tests
python -m pytest job-tests/scheduled-report/ -v
python -m pytest job-tests/batch-prediction/ -v
python -m pytest job-tests/data-processing-pipeline/ -v
python -m pytest job-tests/data-quality-check/ -v
python -m pytest job-tests/knowledge-connector/ -v
python -m pytest job-tests/ml-model-training/ -v
python -m pytest job-tests/hyperparameter-tuning/ -v

# Run with unittest directly
python -m unittest discover -s job-tests -p "test_*.py" -v
```

## Test Categories

Each test file covers:

- **Argument Parsing** — CLI flags, defaults, required args, invalid inputs
- **Core Logic** — business logic for the specific job type (batching, transforms, sync, search spaces, etc.)
- **Output / Reporting** — file generation, JSON serialization, report structure
- **Error Handling** — bad inputs, missing files, retries, edge cases
- **Container Environment** — Python version, GPU env vars, filesystem expectations

## Requirements

- Python 3.10+ (tests are compatible across 3.10–3.12)
- No external dependencies required (stdlib `unittest` only)
