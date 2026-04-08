"""Test inference for Summarization model."""
import pickle, json, re
from sklearn.feature_extraction.text import TfidfVectorizer

class ExtractiveSummarizer:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=500, stop_words="english")
    def fit(self, documents):
        all_sentences = []
        for doc in documents:
            all_sentences.extend(re.split(r'[.!?]+', doc))
        clean = [s.strip() for s in all_sentences if len(s.strip()) > 10]
        self.vectorizer.fit(clean)
        return self
    def predict(self, documents, num_sentences=2):
        results = []
        for doc in documents:
            sentences = [s.strip() for s in re.split(r'[.!?]+', doc) if len(s.strip()) > 10]
            if len(sentences) <= num_sentences:
                results.append(". ".join(sentences) + ".")
                continue
            tfidf = self.vectorizer.transform(sentences)
            scores = tfidf.sum(axis=1).A1
            top_idx = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:num_sentences]
            top_idx.sort()
            results.append(". ".join(sentences[i] for i in top_idx) + ".")
        return results

with open("model.pkl", "rb") as f:
    model = pickle.load(f)
with open("sample_input.json") as f:
    sample = json.load(f)

summaries = model.predict(sample["documents"], num_sentences=sample.get("num_sentences", 2))
print(f"Model type: {type(model).__name__}")
for doc, summary in zip(sample["documents"], summaries):
    print(f"  Input ({len(doc)} chars): '{doc[:80]}...'")
    print(f"  Summary: '{summary}'\n")
print("\n✅ Summarization inference test PASSED")
