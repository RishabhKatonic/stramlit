# Katonic Platform — Real Test Examples

Complete working examples for **Deploy Model**, **Deploy LLM**, and **Fine-Tune Job** wizards.

---

## 📁 File Structure

```
katonic-examples/
│
├── deploy-model/                              # Pre-trained .pkl models for Deploy Model wizard
│   ├── binary-classification/                 # LogisticRegression (736 bytes)
│   ├── regression/                            # LinearRegression (467 bytes)
│   ├── nlp/                                   # TF-IDF + LogisticRegression pipeline (2.6 KB)
│   ├── image-classification/                  # RandomForest on 64-dim features (40 KB)
│   ├── audio-classification/                  # RandomForest on 13 MFCC features (33 KB)
│   ├── text-classification/                   # TF-IDF + MultinomialNB topic classifier (7.8 KB)
│   ├── sentiment-analysis/                    # TF-IDF + LogisticRegression pos/neg/neutral (4.5 KB)
│   ├── text-generation/                       # Markov chain text generator (3.8 KB)
│   ├── summarization/                         # TF-IDF extractive summarizer (3 KB)
│   ├── question-answering/                    # TF-IDF retrieval QA (2.5 KB)
│   ├── fill-mask/                             # Bigram frequency masked word predictor (1 KB)
│   ├── token-classification-ner/              # Rule + pattern based NER (327 bytes)
│   ├── zero-shot-classification/              # TF-IDF cosine similarity classifier (3.1 KB)
│   └── translation/                           # Dictionary-based EN→ES translator (780 bytes)
│
│   Each folder contains:
│     ├── model.pkl              # Serialized model
│     ├── sample_input.json      # Test input data
│     └── test_inference.py      # Verify model works
│
├── deploy-llm/                                # (see Deploy LLM section below)
│
├── fine-tune/
│   └── datasets/                              # Upload any ONE of these in the Fine-Tune wizard
│       ├── training_data.jsonl
│       ├── training_chat_format.jsonl
│       ├── training_data.json
│       ├── training_data.csv
│       └── training_data.parquet
│
└── README.md
```

---

## 1️⃣ Deploy Model — Model Type ↔ Folder Mapping

### All 14 Model Types (matches Create Model wizard dropdown)

| # | Model Type (Dropdown)          | Folder                        | Model File Path                                  | Command for Deploy                                    |
|---|-------------------------------|-------------------------------|--------------------------------------------------|-------------------------------------------------------|
| 1 | **Text Classification**        | `text-classification/`        | `text-classification/model.pkl`                  | `python test_inference.py`                            |
| 2 | **Sentiment Analysis**         | `sentiment-analysis/`         | `sentiment-analysis/model.pkl`                   | `python test_inference.py`                            |
| 3 | **Text Generation**            | `text-generation/`            | `text-generation/model.pkl`                      | `python test_inference.py`                            |
| 4 | **Summarization**              | `summarization/`              | `summarization/model.pkl`                        | `python test_inference.py`                            |
| 5 | **Question Answering**         | `question-answering/`         | `question-answering/model.pkl`                   | `python test_inference.py`                            |
| 6 | **Fill Mask**                  | `fill-mask/`                  | `fill-mask/model.pkl`                            | `python test_inference.py`                            |
| 7 | **Token Classification (NER)** | `token-classification-ner/`   | `token-classification-ner/model.pkl`             | `python test_inference.py`                            |
| 8 | **Zero-Shot Classification**   | `zero-shot-classification/`   | `zero-shot-classification/model.pkl`             | `python test_inference.py`                            |
| 9 | **Image Classification**       | `image-classification/`       | `image-classification/model.pkl`                 | `python test_inference.py`                            |
| 10| **Audio Classification**       | `audio-classification/`       | `audio-classification/model.pkl`                 | `python test_inference.py`                            |
| 11| **Translation**                | `translation/`                | `translation/model.pkl`                          | `python test_inference.py`                            |
| 12| **Binary Classification**      | `binary-classification/`      | `binary-classification/model.pkl`                | `python test_inference.py`                            |
| 13| **Regression**                 | `regression/`                 | `regression/model.pkl`                           | `python test_inference.py`                            |
| 14| **NLP**                        | `nlp/`                        | `nlp/model.pkl`                                  | `python test_inference.py`                            |

### GitHub Source — Form Values

Push the `deploy-model/` folder to a GitHub repo, then fill:

| Field                | Value                                       |
|----------------------|---------------------------------------------|
| **Organization**     | `your-github-org`                           |
| **Repository Name**  | `katonic-models`                            |
| **Branch or Tag**    | Branch                                      |
| **Branch Name**      | `main`                                      |
| **Model File Path**  | `<folder-name>/model.pkl` (from table above)|

### HuggingFace Source — Smallest Real Models

| Model Type                   | HuggingFace Model Name                                   | Size    |
|------------------------------|----------------------------------------------------------|---------|
| Text Classification          | `distilbert-base-uncased-finetuned-sst-2-english`       | ~268 MB |
| Sentiment Analysis           | `cardiffnlp/twitter-roberta-base-sentiment-latest`      | ~499 MB |
| Text Generation              | `sshleifer/tiny-gpt2`                                    | ~500 KB |
| Summarization                | `sshleifer/distilbart-cnn-6-6`                           | ~680 MB |
| Question Answering           | `distilbert-base-cased-distilled-squad`                  | ~261 MB |
| Fill Mask                    | `prajjwal1/bert-tiny`                                    | ~17 MB  |
| Token Classification (NER)   | `dslim/bert-base-NER`                                    | ~433 MB |
| Zero-Shot Classification     | `typeform/distilbert-base-uncased-mnli`                  | ~261 MB |
| Image Classification         | `google/mobilenet_v2_1.0_224`                            | ~14 MB  |
| Audio Classification         | `MIT/ast-finetuned-speech-commands-v2`                   | ~344 MB |
| Translation                  | `Helsinki-NLP/opus-mt-en-es`                             | ~312 MB |
| Binary Classification        | `distilbert-base-uncased-finetuned-sst-2-english`       | ~268 MB |
| Regression                   | `cardiffnlp/twitter-roberta-base-sentiment`              | ~499 MB |
| NLP                          | `prajjwal1/bert-tiny`                                    | ~17 MB  |

> **Smallest overall**: `sshleifer/tiny-gpt2` (~500 KB) or `prajjwal1/bert-tiny` (~17 MB)

---

## 2️⃣ Deploy LLM — Exact Form Values

### HuggingFace Source (smallest LLMs)

| Field                    | Tiny Test                         | Small Test                            |
|--------------------------|-----------------------------------|---------------------------------------|
| **Deployment Name**      | `test-tiny-llm`                  | `test-small-llm`                      |
| **Model Name or HF ID** | `sshleifer/tiny-gpt2`           | `TinyLlama/TinyLlama-1.1B-Chat-v1.0` |
| **Quantization**         | None (Full Precision)            | None (Full Precision)                 |
| **Hardware Type**        | CPU                              | GPU                                   |
| **Size**                 | ~500 KB                          | ~2.2 GB                               |

---

## 3️⃣ Fine-Tune Job — Exact Form Values

### Step 1: Configuration

| Field                | Value                        |
|----------------------|------------------------------|
| **Job Name**         | `test-finetune-tiny`         |
| **Output Model Name**| `test-finetuned-v1`          |

### Step 2: Base Model

| HuggingFace Model ID                          | Size    | Good For             |
|-----------------------------------------------|---------|----------------------|
| `sshleifer/tiny-gpt2`                        | ~500 KB | Fastest smoke test   |
| `prajjwal1/bert-tiny`                        | ~17 MB  | Classification tasks |
| `Qwen/Qwen2-0.5B`                            | ~1 GB   | Real instruction tuning |

### Step 3: Dataset

Upload ONE file from `fine-tune/datasets/`:

| File                          | Format  | Best For                    |
|-------------------------------|---------|------------------------------|
| `training_data.jsonl`         | JSONL   | Standard instruction tuning  |
| `training_chat_format.jsonl`  | JSONL   | Chat-style fine-tuning       |
| `training_data.json`          | JSON    | Alternative format           |
| `training_data.csv`           | CSV     | Spreadsheet-friendly         |
| `training_data.parquet`       | Parquet | Efficient columnar format    |

---

## 🧪 Verify Models Locally

```bash
# Test ALL models
cd deploy-model
for d in */; do echo "=== $d ===" && cd "$d" && python test_inference.py && cd ..; done

# Test a specific model
cd deploy-model/text-classification && python test_inference.py
```

Requires: `pip install scikit-learn numpy`

---

## ⚡ Quick-Start: Fastest Possible Test

1. **Deploy Model** → GitHub → `text-classification/model.pkl` → Text Classification → Deploy
2. **Deploy LLM** → HuggingFace → `sshleifer/tiny-gpt2` → CPU → Deploy
3. **Fine-Tune** → `sshleifer/tiny-gpt2` → Upload `training_data.jsonl` → Start
