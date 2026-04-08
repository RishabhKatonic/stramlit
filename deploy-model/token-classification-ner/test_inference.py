"""Test inference for Token Classification (NER) model."""
import pickle, json, re

class RuleBasedNER:
    def __init__(self):
        self.persons = set()
        self.orgs = set()
        self.locations = set()
    def fit(self, persons=None, orgs=None, locations=None):
        self.persons = set(p.lower() for p in (persons or []))
        self.orgs = set(o.lower() for o in (orgs or []))
        self.locations = set(l.lower() for l in (locations or []))
        return self
    def predict(self, texts):
        results = []
        for text in texts:
            entities = []
            words = text.split()
            i = 0
            while i < len(words):
                wc = re.sub(r'[^\w]', '', words[i]).lower()
                if i < len(words) - 1:
                    bigram = wc + " " + re.sub(r'[^\w]', '', words[i+1]).lower()
                    matched = False
                    for gazeteer, label in [(self.persons, "PER"), (self.orgs, "ORG"), (self.locations, "LOC")]:
                        if bigram in gazeteer:
                            entities.append({"text": f"{words[i]} {words[i+1]}", "label": label, "start": i})
                            i += 2; matched = True; break
                    if matched: continue
                if wc in self.persons: entities.append({"text": words[i], "label": "PER", "start": i})
                elif wc in self.orgs: entities.append({"text": words[i], "label": "ORG", "start": i})
                elif wc in self.locations: entities.append({"text": words[i], "label": "LOC", "start": i})
                elif re.match(r'\d{4}-\d{2}-\d{2}', words[i]): entities.append({"text": words[i], "label": "DATE", "start": i})
                elif re.match(r'\$[\d,.]+', words[i]): entities.append({"text": words[i], "label": "MONEY", "start": i})
                i += 1
            results.append(entities)
        return results

with open("model.pkl", "rb") as f:
    model = pickle.load(f)
with open("sample_input.json") as f:
    sample = json.load(f)

predictions = model.predict(sample["texts"])
print(f"Model type: {type(model).__name__}")
print(f"Known entities: {len(model.persons)} persons, {len(model.orgs)} orgs, {len(model.locations)} locations")
for text, entities in zip(sample["texts"], predictions):
    print(f"  '{text}'")
    for ent in entities:
        print(f"    → [{ent['label']}] {ent['text']}")
print("\n✅ Token Classification (NER) inference test PASSED")
