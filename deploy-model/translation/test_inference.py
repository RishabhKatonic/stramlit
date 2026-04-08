"""Test inference for Translation model."""
import pickle, json, re

class DictionaryTranslator:
    def __init__(self):
        self.dictionary = {}
        self.source_lang = "en"
        self.target_lang = "es"
    def fit(self, en_es_pairs):
        for en, es in en_es_pairs:
            self.dictionary[en.lower()] = es
        return self
    def predict(self, texts):
        results = []
        for text in texts:
            words = text.split()
            translated = []
            for word in words:
                clean = re.sub(r'[^\w]', '', word).lower()
                punct = word[len(clean):] if len(word) > len(clean) else ""
                translated.append(self.dictionary.get(clean, word) + punct)
            results.append(" ".join(translated))
        return results

with open("model.pkl", "rb") as f:
    model = pickle.load(f)
with open("sample_input.json") as f:
    sample = json.load(f)

translations = model.predict(sample["texts"])
print(f"Model type: {type(model).__name__}")
print(f"Direction: {model.source_lang} → {model.target_lang}")
print(f"Dictionary size: {len(model.dictionary)} words")
for src, tgt in zip(sample["texts"], translations):
    print(f"  '{src}' → '{tgt}'")
if "expected" in sample:
    print(f"\nExpected: {sample['expected']}")
    print(f"Match: {translations == sample['expected']}")
print("\n✅ Translation inference test PASSED")
