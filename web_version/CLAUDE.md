# CLAUDE.md — web_version

## Overview

Browser-based handwritten digit recognition app.
Users draw a digit on an HTML5 Canvas; the image is sent to a Python backend (FastAPI) which runs inference and returns the predicted digit with per-class confidence scores.

## Planned stack

| Layer | Technology |
|-------|-----------|
| Frontend | Vanilla HTML + CSS + JavaScript (no framework) |
| Backend | Python FastAPI |
| Model | scikit-learn Random Forest trained on MNIST (same as desktop_version) |
| Communication | REST — POST `/predict` with base64-encoded PNG |

## Planned file structure

```
web_version/
  backend/
    main.py           # FastAPI app — /predict endpoint
    model.py          # load_or_train_model, preprocess_image helpers
    digit_model.pkl   # cached trained model (gitignore candidate)
    requirements.txt  # fastapi, uvicorn, scikit-learn, pillow, numpy
  frontend/
    index.html        # single-page app
    style.css         # optional extracted styles
    app.js            # canvas drawing + fetch logic
```

## Running (planned)

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload   # runs on http://localhost:8000

# Frontend — open in browser (no build step)
open frontend/index.html
# or serve with:
python -m http.server 5500 --directory frontend
```

## API contract

### POST `/predict`

**Request body (JSON)**
```json
{ "image": "<base64-encoded PNG string>" }
```

**Response (JSON)**
```json
{
  "digit": 3,
  "confidence": 0.91,
  "probabilities": [0.01, 0.02, 0.01, 0.91, 0.01, 0.01, 0.01, 0.01, 0.01, 0.00]
}
```

## Frontend behaviour

- 280×280 `<canvas>` with mouse and touch drawing support.
- "Predict" button POSTs the canvas image to `/predict` and displays the result.
- "Clear" button resets the canvas and result display.
- Confidence displayed as a bar chart (CSS / `<progress>` elements) for digits 0–9.

## Preprocessing (backend)

Identical to `desktop_version`:
1. Convert to grayscale and invert (white bg → black).
2. Crop to bounding box of drawn region.
3. Resize to 20×20, pad to 28×28 (MNIST convention).
4. Flatten and normalise to [0, 1].

## Development notes

- The backend can share `digit_model.pkl` with `desktop_version` by adjusting `MODEL_PATH`, or keep its own copy.
- CORS must be enabled on the FastAPI app (`fastapi.middleware.cors.CORSMiddleware`) when the frontend is served from a different origin.
- For production, consider replacing Random Forest with a lightweight CNN exported to ONNX or TensorFlow.js so inference runs entirely in the browser without a backend.
