"""
Handwritten Digit Recognition
-------------------------------
Draw a digit (0-9) on the canvas and click "Predict" to recognize it.
Uses a Random Forest classifier trained on the MNIST dataset.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
from PIL import Image, ImageDraw
import os
import pickle
import threading
import traceback

MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "digit_model.pkl")
CANVAS_SIZE = 280   # Drawing canvas size (pixels)


# ---------------------------------------------------------------------------
# Model helpers
# ---------------------------------------------------------------------------

def train_and_save_model(status_cb):
    """Train a Random Forest on MNIST and persist it to disk."""
    from sklearn.datasets import fetch_openml
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import StandardScaler
    from sklearn.pipeline import Pipeline

    status_cb("Downloading MNIST dataset... (first run only, may take a minute)")

    mnist = fetch_openml("mnist_784", version=1, as_frame=False, parser="auto")
    X, y = mnist.data / 255.0, mnist.target.astype(int)

    # Use 12,000 samples for a good speed/accuracy balance
    X_train, y_train = X[:12000], y[:12000]

    status_cb("Training model on 12,000 samples...")

    model = Pipeline([
        ("scaler", StandardScaler()),
        ("clf",    RandomForestClassifier(n_estimators=150, n_jobs=-1, random_state=42)),
    ])
    model.fit(X_train, y_train)

    # Quick accuracy check on a held-out slice
    acc = model.score(X[60000:62000], y[60000:62000])
    status_cb(f"Model ready  (test accuracy: {acc:.1%})")

    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)

    return model


def load_or_train_model(status_cb):
    """Load the cached model, or train a new one if it does not exist."""
    if os.path.exists(MODEL_PATH):
        status_cb("Loading saved model...")
        with open(MODEL_PATH, "rb") as f:
            model = pickle.load(f)
        status_cb("Model ready  (loaded from cache)")
        return model
    return train_and_save_model(status_cb)


# ---------------------------------------------------------------------------
# Image preprocessing
# ---------------------------------------------------------------------------

def preprocess_canvas(pil_img):
    """
    Convert a PIL image (drawn on the canvas) to a 28x28 flat numpy vector
    that matches the MNIST format: white digit on black background.
    """
    gray = pil_img.convert("L")

    # Canvas: white background + black strokes -> invert to match MNIST convention
    arr = np.array(gray)
    arr = 255 - arr

    # Crop to bounding box of the drawn region
    rows = np.any(arr > 20, axis=1)
    cols = np.any(arr > 20, axis=0)
    if not rows.any():
        return None  # nothing drawn
    rmin, rmax = np.where(rows)[0][[0, -1]]
    cmin, cmax = np.where(cols)[0][[0, -1]]
    arr = arr[rmin:rmax+1, cmin:cmax+1]

    # Resize to 20x20 and place in a 28x28 frame with 4px padding (MNIST style)
    img_cropped = Image.fromarray(arr).resize((20, 20), Image.LANCZOS)
    canvas28 = Image.new("L", (28, 28), 0)
    canvas28.paste(img_cropped, (4, 4))

    return np.array(canvas28).reshape(1, -1) / 255.0


# ---------------------------------------------------------------------------
# GUI
# ---------------------------------------------------------------------------

class DigitRecognizer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Handwritten Digit Recognition")
        self.resizable(False, False)

        self.model = None
        self.pil_image = Image.new("RGB", (CANVAS_SIZE, CANVAS_SIZE), "white")
        self.pil_draw  = ImageDraw.Draw(self.pil_image)
        self.last_x = self.last_y = None

        self._build_ui()

        # Load/train model in a background thread so the window stays responsive
        threading.Thread(target=self._load_model_bg, daemon=True).start()

    # ---- UI construction --------------------------------------------------

    def _build_ui(self):
        pad = dict(padx=10, pady=6)

        tk.Label(self, text="Handwritten Digit Recognition",
                 font=("Helvetica", 16, "bold")).pack(**pad)

        # Drawing canvas
        self.canvas = tk.Canvas(self, width=CANVAS_SIZE, height=CANVAS_SIZE,
                                bg="white", cursor="crosshair",
                                highlightthickness=2, highlightbackground="#999")
        self.canvas.pack(padx=10, pady=4)
        self.canvas.bind("<ButtonPress-1>",   self._on_press)
        self.canvas.bind("<B1-Motion>",       self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)

        # Prediction display
        self.pred_var = tk.StringVar(value="Draw a digit, then click Predict")
        tk.Label(self, textvariable=self.pred_var,
                 font=("Helvetica", 22, "bold"), fg="#1a73e8",
                 width=34).pack(**pad)

        # Confidence bars (one per digit 0-9)
        bar_frame = tk.Frame(self)
        bar_frame.pack(fill="x", padx=12)
        self.bars = []
        for i in range(10):
            row = tk.Frame(bar_frame)
            row.pack(fill="x", pady=1)
            tk.Label(row, text=str(i), width=2, font=("Courier", 10)).pack(side="left")
            bar = ttk.Progressbar(row, length=220, maximum=100, mode="determinate")
            bar.pack(side="left", padx=4)
            lbl = tk.Label(row, text="0.0%", width=6, font=("Courier", 10))
            lbl.pack(side="left")
            self.bars.append((bar, lbl))

        # Buttons — Predict starts disabled until the model is ready
        btn_frame = tk.Frame(self)
        btn_frame.pack(**pad)
        self.predict_btn = tk.Button(
            btn_frame, text="Predict", width=12,
            bg="#aaa", fg="white", font=("Helvetica", 11, "bold"),
            state=tk.DISABLED, command=self._predict)
        self.predict_btn.pack(side="left", padx=6)
        tk.Button(btn_frame, text="Clear", width=12,
                  font=("Helvetica", 11),
                  command=self._clear).pack(side="left", padx=6)

        # Loading progress bar (shown while model is loading)
        self.loading_bar = ttk.Progressbar(self, mode="indeterminate", length=300)
        self.loading_bar.pack(pady=(0, 4))
        self.loading_bar.start(15)

        # Status bar
        self.status_var = tk.StringVar(value="Initialising...")
        tk.Label(self, textvariable=self.status_var,
                 font=("Helvetica", 9), fg="#555",
                 anchor="w").pack(fill="x", padx=10, pady=(0, 6))

    # ---- Background model loading ----------------------------------------

    def _load_model_bg(self):
        """Runs in a worker thread; uses after() to push UI updates to main thread."""
        def status(msg):
            self.after(0, self.status_var.set, msg)

        try:
            model = load_or_train_model(status)
            self.model = model
            # Enable the Predict button on the main thread
            self.after(0, self._on_model_ready)
        except Exception:
            err = traceback.format_exc()
            self.after(0, self.status_var.set, "ERROR — see console for details")
            print(err)

    def _on_model_ready(self):
        """Called on the main thread once the model is fully loaded."""
        self.loading_bar.stop()
        self.loading_bar.pack_forget()
        self.predict_btn.config(state=tk.NORMAL, bg="#1a73e8")

    # ---- Drawing event handlers ------------------------------------------

    def _on_press(self, event):
        self.last_x, self.last_y = event.x, event.y

    def _on_drag(self, event):
        x, y = event.x, event.y
        if self.last_x is not None:
            r = 10  # brush radius
            self.canvas.create_oval(x-r, y-r, x+r, y+r,
                                    fill="black", outline="black")
            self.canvas.create_line(self.last_x, self.last_y, x, y,
                                    fill="black", width=r*2,
                                    capstyle=tk.ROUND, smooth=True)
            self.pil_draw.ellipse([x-r, y-r, x+r, y+r], fill="black")
            self.pil_draw.line([self.last_x, self.last_y, x, y],
                               fill="black", width=r*2)
        self.last_x, self.last_y = x, y

    def _on_release(self, _event):
        self.last_x = self.last_y = None

    # ---- Predict ---------------------------------------------------------

    def _predict(self):
        flat = preprocess_canvas(self.pil_image)
        if flat is None:
            messagebox.showinfo("Empty canvas", "Please draw a digit first.")
            return

        probas = self.model.predict_proba(flat)[0]
        digit  = int(np.argmax(probas))
        conf   = probas[digit]

        self.pred_var.set(f"Prediction: {digit}   ({conf:.1%} confidence)")

        for i, (bar, lbl) in enumerate(self.bars):
            p = probas[i] * 100
            bar["value"] = p
            lbl.config(text=f"{p:.1f}%",
                       fg="#1a73e8" if i == digit else "#333")

    # ---- Clear -----------------------------------------------------------

    def _clear(self):
        self.canvas.delete("all")
        self.pil_image = Image.new("RGB", (CANVAS_SIZE, CANVAS_SIZE), "white")
        self.pil_draw  = ImageDraw.Draw(self.pil_image)
        self.pred_var.set("Draw a digit, then click Predict")
        for bar, lbl in self.bars:
            bar["value"] = 0
            lbl.config(text="0.0%", fg="#333")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app = DigitRecognizer()
    app.mainloop()
