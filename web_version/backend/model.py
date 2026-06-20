"""
Model helpers — shared between training and inference.
"""

import os
import pickle
import io
import base64
import numpy as np
from PIL import Image

# Point to the shared model file in the parent directory (same one used by desktop_version)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "..", "..", "digit_model.pkl")


def train_and_save_model(status_cb=print):
    from sklearn.datasets import fetch_openml
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import StandardScaler
    from sklearn.pipeline import Pipeline

    status_cb("Downloading MNIST dataset... (first run only, may take a minute)")
    mnist = fetch_openml("mnist_784", version=1, as_frame=False, parser="auto")
    X, y = mnist.data / 255.0, mnist.target.astype(int)
    X_train, y_train = X[:12000], y[:12000]

    status_cb("Training model on 12,000 samples...")
    model = Pipeline([
        ("scaler", StandardScaler()),
        ("clf",    RandomForestClassifier(n_estimators=150, n_jobs=-1, random_state=42)),
    ])
    model.fit(X_train, y_train)

    acc = model.score(X[60000:62000], y[60000:62000])
    status_cb(f"Model ready (test accuracy: {acc:.1%})")

    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)
    return model


def load_or_train_model(status_cb=print):
    if os.path.exists(MODEL_PATH):
        status_cb("Loading saved model...")
        with open(MODEL_PATH, "rb") as f:
            model = pickle.load(f)
        status_cb("Model ready (loaded from cache)")
        return model
    return train_and_save_model(status_cb)


def preprocess_base64(b64_string: str):
    """
    Decode a base64 PNG from the browser canvas and return a 28x28 flat vector
    matching MNIST format (white digit on black background).
    """
    # Strip data URL prefix if present: "data:image/png;base64,..."
    if "," in b64_string:
        b64_string = b64_string.split(",", 1)[1]

    img_bytes = base64.b64decode(b64_string)
    pil_img = Image.open(io.BytesIO(img_bytes)).convert("RGBA")

    # Flatten alpha onto white background, then convert to grayscale
    background = Image.new("RGBA", pil_img.size, (255, 255, 255, 255))
    background.paste(pil_img, mask=pil_img.split()[3])
    gray = background.convert("L")

    arr = np.array(gray)
    arr = 255 - arr  # invert: white bg → black bg (MNIST convention)

    # Crop to bounding box
    rows = np.any(arr > 20, axis=1)
    cols = np.any(arr > 20, axis=0)
    if not rows.any():
        return None  # nothing drawn

    rmin, rmax = np.where(rows)[0][[0, -1]]
    cmin, cmax = np.where(cols)[0][[0, -1]]
    arr = arr[rmin:rmax+1, cmin:cmax+1]

    # Resize to 20x20, pad to 28x28
    img_cropped = Image.fromarray(arr).resize((20, 20), Image.LANCZOS)
    canvas28 = Image.new("L", (28, 28), 0)
    canvas28.paste(img_cropped, (4, 4))

    return np.array(canvas28).reshape(1, -1) / 255.0
