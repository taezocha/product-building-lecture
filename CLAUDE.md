# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What's in this directory

This is a solo-builder practice workspace (조코딩 1인 빌더 실습). It contains independent mini-projects, not a single unified codebase.

| File | Description |
|------|-------------|
| `index.html` | Sports Mentality Database Platform — static MVP landing page (no build step) |
| `digit_recognition.py` | Handwritten digit recognizer — tkinter GUI + sklearn Random Forest on MNIST |
| `digit_model.pkl` | Cached trained model (auto-generated on first run, gitignore candidate) |

## Running things

**Landing page** — open `index.html` directly in a browser. No server required.

**Digit recognizer**
```bash
# First run downloads MNIST and trains the model (~1-2 min)
python digit_recognition.py

# Required packages (Python 3.x)
pip install numpy pillow scikit-learn pandas
```

The trained model is cached to `digit_model.pkl` so subsequent runs load instantly.

## index.html architecture

Single-file static page with no framework or bundler.

- **CSS**: custom properties (`--bg`, `--primary`, etc.) in `:root`; responsive via two `@media` breakpoints (980px, 720px)
- **i18n**: all user-facing strings live in a `translations` object (`ko`/`en`). The `ids` map connects translation keys to DOM element IDs. `setLanguage(lang)` swaps all text at once. The KR/EN toggle button drives this.
- To add a new translated string: add the key to both `translations.ko` and `translations.en`, add the element ID to `ids`, and set the element's `id` in the HTML.

## digit_recognition.py architecture

Three layers:

1. **Model layer** (`load_or_train_model`, `train_and_save_model`) — loads `digit_model.pkl` if it exists, otherwise downloads MNIST via `fetch_openml` and trains a `StandardScaler → RandomForestClassifier` pipeline. Runs in a background thread.
2. **Preprocessing** (`preprocess_canvas`) — inverts the canvas image (white bg → black bg), crops to bounding box, resizes to 20×20, pads to 28×28 to match MNIST convention.
3. **GUI** (`DigitRecognizer(tk.Tk)`) — tkinter window with a 280×280 drawing canvas, prediction label, per-digit confidence bars, Predict/Clear buttons. Predict button is disabled until the model is ready; a `ttk.Progressbar` in indeterminate mode shows loading progress.

UI updates from the background thread are always dispatched via `self.after(0, ...)` to avoid cross-thread tkinter crashes.
