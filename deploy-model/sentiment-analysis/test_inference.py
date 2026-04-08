"""Test inference for Sentiment Analysis model."""
import pickle, json

with open("model.pkl", "rb") as f:
    pipeline = pickle.load(f)

with open("sample_input.json") as f:
    sample = json.load(f)

texts = sample["texts"]
predictions = pipeline.predict(texts)
probabilities = pipeline.predict_proba(texts)

print(f"Pipeline steps: {[step[0] for step in pipeline.steps]}")
print(f"Sentiment classes: {pipeline.classes_.tolist()}")
for text, pred, prob in zip(texts, predictions, probabilities):
    print(f"  \'{text}\' → {pred} (confidence: {max(prob):.2%})")
print(f"\nExpected: {sample['expected']}")
print(f"Match: {list(predictions) == sample['expected']}")
print("\n✅ Sentiment Analysis inference test PASSED")
