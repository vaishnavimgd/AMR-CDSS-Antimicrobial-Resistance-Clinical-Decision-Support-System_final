"""
Script to generate a dummy AMR prediction model for testing.

Creates a simple scikit-learn model that takes a 5-element gene vector
and predicts resistance class (0=Susceptible, 1=Intermediate, 2=Resistant)
for three antibiotics: Ciprofloxacin, Ampicillin, Tetracycline.

Usage:
    python create_dummy_model.py
"""

import numpy as np
import joblib
from sklearn.tree import DecisionTreeClassifier
from sklearn.multioutput import MultiOutputClassifier

# ─── Training data ───────────────────────────────────────────────────────────
# Gene vectors: [geneA, geneB, geneC, geneD, geneE]
# Labels: [ciprofloxacin, ampicillin, tetracycline]
#   0 = Susceptible, 1 = Intermediate, 2 = Resistant

X_train = np.array([
    [1, 1, 0, 0, 0],
    [0, 0, 0, 0, 0],
    [1, 0, 1, 0, 0],
    [0, 1, 0, 1, 0],
    [1, 1, 1, 1, 1],
    [0, 0, 1, 0, 1],
    [1, 0, 0, 1, 0],
    [0, 1, 1, 0, 0],
])

y_train = np.array([
    [2, 2, 0],  # geneA+B → Resistant to cipro & amp
    [0, 0, 0],  # no genes → Susceptible to all
    [2, 0, 1],  # geneA+C → Resistant cipro, Intermediate tet
    [0, 1, 2],  # geneB+D → Intermediate amp, Resistant tet
    [2, 2, 2],  # all genes → Resistant to all
    [1, 0, 2],  # geneC+E → Intermediate cipro, Resistant tet
    [2, 1, 0],  # geneA+D → Resistant cipro, Intermediate amp
    [1, 2, 0],  # geneB+C → Intermediate cipro, Resistant amp
])

# ─── Train model ─────────────────────────────────────────────────────────────
model = MultiOutputClassifier(DecisionTreeClassifier(random_state=42))
model.fit(X_train, y_train)

# ─── Save ─────────────────────────────────────────────────────────────────────
joblib.dump(model, "model.pkl")
print("Dummy model saved to model.pkl")

# ─── Quick test ───────────────────────────────────────────────────────────────
test_input = np.array([[1, 1, 0, 0, 0]])
prediction = model.predict(test_input)
labels = {0: "Susceptible", 1: "Intermediate", 2: "Resistant"}
antibiotics = ["Ciprofloxacin", "Ampicillin", "Tetracycline"]
for ab, pred in zip(antibiotics, prediction[0]):
    print(f"  {ab}: {labels[pred]}")
