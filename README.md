# Katonic Platform — Real Test Examples

Complete working examples for **Deploy Model**, **Deploy LLM**, and **Fine-Tune Job** wizards.

---

## 📁 File Structure

```
katonic-examples/
│
├── deploy-model/                          # Pre-trained .pkl models for Deploy Model wizard
│   ├── binary-classification/
│   │   ├── model.pkl                      # LogisticRegression (736 bytes)
│   │   ├── sample_input.json              # Test input data
│   │   └── test_inference.py              # Verify model works
│   ├── regression/
│   │   ├── model.pkl                      # LinearRegression (467 bytes)
│   │   ├── sample_input.json
│   │   └── test_inference.py
│   ├── nlp/
│   │   ├── model.pkl                      # TF-IDF + LogisticRegression pipeline (2.6 KB)
│   │   ├── sample_input.json
│   │   └── test_inference.py
│   ├── image-classification/
│   │   ├── model.pkl                      # RandomForest on 64-dim features (40 KB)
│   │   ├── sample_input.json
│   │   └── test_inference.py
│   └── audio-classification/
│       ├── model.pkl                      # RandomForest on 13 MFCC features (33 KB)
│       ├── sample_input.json
│       └── test_inference.py
│
├── fine-tune/
│   └── datasets/                          # Upload any ONE of these in the Fine-Tune wizard
│       ├── training_data.jsonl            # ← Recommended (instruction/input/output format)
│       ├── training_chat_format.jsonl     # ← For chat-style fine-tuning (messages format)
│       ├── training_data.json
│       ├── training_data.csv
│       └── training_data.parquet
│
└── README.md
```

---

## 1️⃣ Deploy Model — Exact Form Values

### Option A: GitHub Source (use .pkl files from this zip)

Push any model folder to a GitHub repo, then fill the form:

| Field                  | Binary Classification          | Regression              | NLP                        | Image Classification          | Audio Classification          |
|------------------------|-------------------------------|-------------------------|----------------------------|-------------------------------|-------------------------------|
| **Model Type**         | Binary Classification          | Regression              | NLP                        | Image Classification          | Audio Classification          |
| **Organization**       | `your-github-org`             | `your-github-org`       | `your-github-org`          | `your-github-org`             | `your-github-org`             |
| **Repository Name**    | `katonic-models`              | `katonic-models`        | `katonic-models`           | `katonic-models`              | `katonic-models`              |
| **Branch or Tag**      | Branch                        | Branch                  | Branch                     | Branch                        | Branch                        |
| **Branch Name**        | `main`                        | `main`                  | `main`                     | `main`                        | `main`                        |
| **Model File Path**    | `binary-classification/model.pkl` | `regression/model.pkl` | `nlp/model.pkl`        | `image-classification/model.pkl` | `audio-classification/model.pkl` |

### Option B: HuggingFace Source (smallest real models)

| Model Type              | HuggingFace Model Name                                     | Size    |
|-------------------------|-------------------------------------------------------------|---------|
| Binary Classification   | `distilbert-base-uncased-finetuned-sst-2-english`          | ~268 MB |
| Regression              | `cardiffnlp/twitter-roberta-base-sentiment`                | ~499 MB |
| NLP                     | `prajjwal1/bert-tiny`                                       | ~17 MB  |
| Image Classification    | `google/mobilenet_v2_1.0_224`                               | ~14 MB  |
| Audio Classification    | `MIT/ast-finetuned-speech-commands-v2`                     | ~344 MB |

> **Smallest overall**: Use `prajjwal1/bert-tiny` (17 MB) for a quick NLP test.

---

## 2️⃣ Deploy LLM — Exact Form Values

### HuggingFace Source (smallest LLMs that actually work)

| Field                         | Tiny Test                         | Small Test                          |
|-------------------------------|-----------------------------------|-------------------------------------|
| **Deployment Name**           | `test-tiny-llm`                  | `test-small-llm`                    |
| **Model Name or HF ID**      | `sshleifer/tiny-gpt2`           | `TinyLlama/TinyLlama-1.1B-Chat-v1.0` |
| **Model Type**                | Inference (LLM)                  | Inference (LLM)                     |
| **Quantization**              | None (Full Precision)            | None (Full Precision)               |
| **Hardware Type**             | CPU                              | GPU                                 |
| **Size**                      | ~500 KB                          | ~2.2 GB                             |

> **Fastest test**: `sshleifer/tiny-gpt2` (~500 KB, runs on CPU).
> **Realistic small test**: `TinyLlama/TinyLlama-1.1B-Chat-v1.0` (~2.2 GB, needs 1 GPU).
> **Other small options**: `microsoft/phi-1_5` (2.8 GB), `Qwen/Qwen2-0.5B` (1 GB).

### Local Model Source

| Field                   | Value                                      |
|-------------------------|--------------------------------------------|
| **Deployment Name**     | `test-local-llm`                           |
| **Model Name or HF ID** | `TinyLlama/TinyLlama-1.1B-Chat-v1.0`     |
| **Model Type**          | Inference (LLM)                            |
| **Storage Dataset**     | (your pre-uploaded volume, e.g. `CDDC`)    |
| **Model Path**          | `models/tinyllama-1.1b`                    |

### Custom vLLM Source

| Field                   | Value                                      |
|-------------------------|--------------------------------------------|
| **Deployment Name**     | `test-custom-vllm`                         |
| **Model Name or HF ID** | `Qwen/Qwen2-0.5B`                        |
| **Model Type**          | Inference (LLM)                            |
| **Quantization**        | None (Full Precision)                      |
| **Hardware Type**       | GPU                                        |
| **GPU Configuration**   | 1x (smallest available)                    |

### NVIDIA NIM Source

| Field                       | Value                                               |
|-----------------------------|-----------------------------------------------------|
| **Deployment Name**         | `test-nim-llm`                                      |
| **NIM Model Endpoint**      | `nim/meta/llama-3.1-8b-instruct`                   |
| **Model Type**              | Inference (LLM)                                     |
| **NVIDIA Connection Provider** | (select your provider)                           |
| **Connection Name**         | `my-nvidia-key`                                     |
| **NIM Container Image**     | `nvcr.io/nim/meta/llama-3.1-8b-instruct:latest`   |

---

## 3️⃣ Fine-Tune Job — Exact Form Values

### Step 1: Configuration

| Field                | Value                        |
|----------------------|------------------------------|
| **Job Name**         | `test-finetune-tiny`         |
| **Output Model Name**| `test-finetuned-v1`          |

### Step 2: Base Model (smallest options)

| HuggingFace Model ID                          | Size    | Good For             |
|-----------------------------------------------|---------|----------------------|
| `sshleifer/tiny-gpt2`                        | ~500 KB | Fastest smoke test   |
| `prajjwal1/bert-tiny`                        | ~17 MB  | Classification tasks |
| `Qwen/Qwen2-0.5B`                            | ~1 GB   | Real instruction tuning |
| `TinyLlama/TinyLlama-1.1B-Chat-v1.0`        | ~2.2 GB | Real chat tuning     |

> **Recommended for quick test**: `sshleifer/tiny-gpt2`
> **Recommended for realistic test**: `Qwen/Qwen2-0.5B`

### Step 3: Dataset

Upload ONE of these files from the `fine-tune/datasets/` folder:

| File                          | Format  | Best For                    |
|-------------------------------|---------|------------------------------|
| `training_data.jsonl`         | JSONL   | Standard instruction tuning  |
| `training_chat_format.jsonl`  | JSONL   | Chat-style fine-tuning       |
| `training_data.json`          | JSON    | Alternative format           |
| `training_data.csv`           | CSV     | Spreadsheet-friendly         |
| `training_data.parquet`       | Parquet | Efficient columnar format    |

All datasets contain **20 real instruction-following examples** covering: summarization, translation, sentiment classification, entity extraction, code generation, grammar correction, SQL writing, topic classification, and more.

**Dataset columns**: `instruction`, `input`, `output`
**Chat format columns**: `messages` (array of `{role, content}` objects)

---

## 🧪 Verify Models Locally

```bash
# Test any model
cd deploy-model/binary-classification && python test_inference.py
cd deploy-model/regression && python test_inference.py
cd deploy-model/nlp && python test_inference.py
cd deploy-model/image-classification && python test_inference.py
cd deploy-model/audio-classification && python test_inference.py
```

Requires: `pip install scikit-learn numpy`

---

## ⚡ Quick-Start: Fastest Possible Test

1. **Deploy Model** → HuggingFace → `prajjwal1/bert-tiny` → NLP → Deploy
2. **Deploy LLM** → HuggingFace → `sshleifer/tiny-gpt2` → CPU → Deploy
3. **Fine-Tune** → `sshleifer/tiny-gpt2` → Upload `training_data.jsonl` → Start
