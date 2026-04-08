"""Test inference for Question Answering model."""
import pickle, json, re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

class TfidfQuestionAnswerer:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=500, stop_words="english")
    def fit(self, passages):
        self.passages = passages
        all_sents = []
        for p in passages:
            all_sents.extend(re.split(r'[.!?]+', p))
        clean = [s.strip() for s in all_sents if len(s.strip()) > 5]
        self.vectorizer.fit(clean)
        return self
    def predict(self, questions, contexts):
        answers = []
        for question, context in zip(questions, contexts):
            sentences = [s.strip() for s in re.split(r'[.!?]+', context) if len(s.strip()) > 5]
            if not sentences:
                answers.append({"answer": "", "score": 0.0}); continue
            q_vec = self.vectorizer.transform([question])
            s_vecs = self.vectorizer.transform(sentences)
            scores = (s_vecs @ q_vec.T).toarray().flatten()
            best_idx = int(np.argmax(scores))
            answers.append({"answer": sentences[best_idx], "score": round(float(scores[best_idx]), 4)})
        return answers

with open("model.pkl", "rb") as f:
    model = pickle.load(f)
with open("sample_input.json") as f:
    sample = json.load(f)

answers = model.predict(sample["questions"], sample["contexts"])
print(f"Model type: {type(model).__name__}")
for q, a in zip(sample["questions"], answers):
    print(f"  Q: '{q}'")
    print(f"  A: '{a['answer']}' (score: {a['score']})\n")
print("\n✅ Question Answering inference test PASSED")
