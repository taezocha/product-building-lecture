# CLAUDE.md — desktop_version

## Overview

Tkinter-based desktop app for handwritten digit recognition.
Trains / loads a scikit-learn Random Forest on MNIST and lets the user draw a digit on a canvas.

## Files

| File | Description |
|------|-------------|
| `digit_recognition.py` | Main entry point — GUI + model loading |
| `digit_model.pkl` | Cached trained model (auto-generated on first run, gitignore candidate) |

## Architecture

Three layers:

1. **Model layer** (`load_or_train_model`, `train_and_save_model`)
   - Loads `digit_model.pkl` if it exists; otherwise downloads MNIST via `fetch_openml` and trains a `StandardScaler → RandomForestClassifier` pipeline.
   - Runs in a background thread so the UI stays responsive.

2. **Preprocessing** (`preprocess_canvas`)
   - Inverts canvas image (white bg → black), crops to bounding box, resizes to 20×20, pads to 28×28 — matching MNIST convention.

3. **GUI** (`DigitRecognizer(tk.Tk)`)
   - 280×280 drawing canvas, prediction label, per-digit confidence bars (0–9), Predict / Clear buttons.
   - Predict button disabled until model is ready; `ttk.Progressbar` (indeterminate) shows loading state.
   - All background-thread UI updates dispatched via `self.after(0, ...)`.

## Running

```bash
# First run: downloads MNIST and trains the model (~1-2 min)
python digit_recognition.py

# Required packages
pip install numpy pillow scikit-learn pandas
```

## Key constants

| Name | Value | Purpose |
|------|-------|---------|
| `CANVAS_SIZE` | 280 | Drawing canvas width/height in pixels |
| `n_estimators` | 150 | Random Forest tree count |
| Training samples | 12,000 | Subset of MNIST for speed/accuracy balance |

## Development notes

- Model is a `sklearn.pipeline.Pipeline`: `StandardScaler` → `RandomForestClassifier`.
- Brush radius is 10 px; both oval and line primitives are drawn in sync on the tkinter canvas and the backing PIL image.
- To retrain from scratch, delete `digit_model.pkl` and rerun the script.
