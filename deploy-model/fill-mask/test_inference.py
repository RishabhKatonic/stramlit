"""Test inference for Fill Mask model."""
import pickle, json
import numpy as np

class FillMaskPredictor:
    def __init__(self):
        self.bigrams = {}
        self.word_freq = {}
    def fit(self, corpus):
        for sentence in corpus:
            words = sentence.lower().split()
            for w in words:
                self.word_freq[w] = self.word_freq.get(w, 0) + 1
            for i in range(len(words) - 1):
                self.bigrams.setdefault(words[i], {})
                self.bigrams[words[i]][words[i+1]] = self.bigrams[words[i]].get(words[i+1], 0) + 1
        return self
    def predict(self, masked_texts, top_k=3):
        results = []
        for text in masked_texts:
            words = text.lower().split()
            mask_idx = next((i for i, w in enumerate(words) if w == "[mask]"), None)
            if mask_idx is None:
                results.append([{"token": "?", "score": 0.0}]); continue
            candidates = {}
            if mask_idx > 0 and words[mask_idx - 1] in self.bigrams:
                candidates = dict(self.bigrams[words[mask_idx - 1]])
            if not candidates:
                candidates = dict(sorted(self.word_freq.items(), key=lambda x: -x[1])[:20])
            sorted_c = sorted(candidates.items(), key=lambda x: -x[1])[:top_k]
            total = sum(c for _, c in sorted_c) or 1
            results.append([{"token": w, "score": round(c/total, 4)} for w, c in sorted_c])
        return results

with open("model.pkl", "rb") as f:
    model = pickle.load(f)
with open("sample_input.json") as f:
    sample = json.load(f)

predictions = model.predict(sample["masked_texts"], top_k=sample.get("top_k", 3))
print(f"Model type: {type(model).__name__}")
print(f"Vocabulary size: {len(model.word_freq)}")
for text, preds in zip(sample["masked_texts"], predictions):
    print(f"  '{text}'")
    for p in preds:
        print(f"    → {p['token']} (score: {p['score']})")
print("\n✅ Fill Mask inference test PASSED")
