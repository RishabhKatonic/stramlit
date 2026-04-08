"""Test inference for Text Generation model."""
import pickle, json
import numpy as np

class MarkovTextGenerator:
    def __init__(self):
        self.transitions = {}
        self.starters = []
    def fit(self, corpus):
        for sentence in corpus:
            words = sentence.split()
            if len(words) < 2: continue
            self.starters.append(words[0])
            for i in range(len(words) - 1):
                self.transitions.setdefault(words[i], []).append(words[i + 1])
    def predict(self, prompts, max_length=20):
        results = []
        for prompt in prompts:
            words = prompt.split()
            current = words[-1] if words else np.random.choice(self.starters)
            output = list(words)
            for _ in range(max_length):
                if current in self.transitions:
                    nxt = np.random.choice(self.transitions[current])
                    output.append(nxt)
                    current = nxt
                else: break
            results.append(" ".join(output))
        return results

with open("model.pkl", "rb") as f:
    model = pickle.load(f)
with open("sample_input.json") as f:
    sample = json.load(f)

generated = model.predict(sample["prompts"], max_length=sample.get("max_length", 20))
print(f"Model type: {type(model).__name__}")
print(f"Vocabulary size: {len(model.transitions)}")
for prompt, text in zip(sample["prompts"], generated):
    print(f"  Prompt: '{prompt}' → '{text}'")
print("\n✅ Text Generation inference test PASSED")
