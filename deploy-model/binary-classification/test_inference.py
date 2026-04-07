"""Test inference for Binary Classification model."""
import pickle, json, numpy as np

# Load model
with open("model.pkl", "rb") as f:
    model = pickle.load(f)

# Load sample input
with open("sample_input.json") as f:
    sample = json.load(f)

X = np.array(sample["features"])
predictions = model.predict(X)
probabilities = model.predict_proba(X)

print(f"Model type: {type(model).__name__}")
print(f"Input shape: {X.shape}")
print(f"Predictions: {predictions.tolist()}")
print(f"Probabilities: {probabilities.tolist()}")
print(f"Expected:    {sample['expected']}")
print(f"Match: {(predictions == np.array(sample['expected'])).all()}")
print("\n✅ Binary Classification inference test PASSED")
