"""Test inference for Image Classification model."""
import pickle, json, numpy as np

with open("model.pkl", "rb") as f:
    model = pickle.load(f)

with open("sample_input.json") as f:
    sample = json.load(f)

X = np.array(sample["features"])
predictions = model.predict(X)
probabilities = model.predict_proba(X)

print(f"Model type: {type(model).__name__}")
print(f"Classes: {model.classes_.tolist()}")
print(f"Input shape: {X.shape}")
print(f"Predictions: {predictions.tolist()}")
print(f"Probabilities: {probabilities.round(3).tolist()}")
print("\n✅ Image Classification inference test PASSED")
