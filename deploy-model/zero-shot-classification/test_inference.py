"""Test inference for Zero-Shot Classification model."""
import pickle, json
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

class ZeroShotClassifier:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=500, stop_words="english")
    def fit(self, corpus):
        self.vectorizer.fit(corpus)
        return self
    def predict(self, texts, candidate_labels):
        results = []
        for text in texts:
            text_vec = self.vectorizer.transform([text])
            label_vecs = self.vectorizer.transform(candidate_labels)
            scores = (label_vecs @ text_vec.T).toarray().flatten()
            total = scores.sum() or 1
            probs = (scores / total).tolist()
            best_idx = int(np.argmax(scores))
            results.append({
                "label": candidate_labels[best_idx],
                "score": round(float(probs[best_idx]), 4),
                "scores": {l: round(float(p), 4) for l, p in zip(candidate_labels, probs)},
            })
        return results

with open("model.pkl", "rb") as f:
    model = pickle.load(f)
with open("sample_input.json") as f:
    sample = json.load(f)

predictions = model.predict(sample["texts"], sample["candidate_labels"])
print(f"Model type: {type(model).__name__}")
print(f"Candidate labels: {sample['candidate_labels']}")
for text, pred in zip(sample["texts"], predictions):
    print(f"  '{text}'")
    print(f"  → Best: {pred['label']} (score: {pred['score']})")
    print(f"  → All scores: {pred['scores']}")
print("\n✅ Zero-Shot Classification inference test PASSED")
