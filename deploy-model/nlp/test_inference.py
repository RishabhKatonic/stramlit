"""Test inference for NLP Text Classification model."""
import pickle, json

with open("model.pkl", "rb") as f:
    pipeline = pickle.load(f)

with open("sample_input.json") as f:
    sample = json.load(f)

texts = sample["texts"]
predictions = pipeline.predict(texts)
probabilities = pipeline.predict_proba(texts)

print(f"Pipeline steps: {[step[0] for step in pipeline.steps]}")
for text, pred, prob in zip(texts, predictions, probabilities):
    label = "Positive" if pred == 1 else "Negative"
    print(f"  '{text}' → {label} (confidence: {max(prob):.2%})")
print(f"\nExpected: {sample['expected']}")
print(f"Match: {(predictions == sample['expected']).all()}")
print("\n✅ NLP inference test PASSED")
