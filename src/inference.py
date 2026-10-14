from pathlib import Path

import joblib
import numpy as np


MODEL_PATH = Path("/model/iris_model.joblib")


def main():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Model not found: {MODEL_PATH}. "
            "Run the training container first."
        )

    print("Loading trained model...")

    artifact = joblib.load(MODEL_PATH)

    model = artifact["model"]
    target_names = artifact["target_names"]

    sample = np.array([[5.1, 3.5, 1.4, 0.2]])

    prediction = model.predict(sample)[0]
    probabilities = model.predict_proba(sample)[0]

    print(f"Input: {sample.tolist()[0]}")
    print(f"Predicted class ID: {prediction}")
    print(f"Predicted flower: {target_names[prediction]}")
    print(f"Probabilities: {probabilities}")


if __name__ == "__main__":
    main()
