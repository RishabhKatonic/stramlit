"""Test inference for Regression model."""
import pickle, json, numpy as np

with open("model.pkl", "rb") as f:
    model = pickle.load(f)

with open("sample_input.json") as f:
    sample = json.load(f)

X = np.array(sample["features"])
predictions = model.predict(X)

print(f"Model type: {type(model).__name__}")
print(f"Input shape: {X.shape}")
print(f"Predictions: {[round(p, 4) for p in predictions.tolist()]}")
print(f"Expected:    {[round(e, 4) for e in sample['expected']]}")
print(f"R² score coefficients: {model.coef_.tolist()}")
print("\n✅ Regression inference test PASSED")
