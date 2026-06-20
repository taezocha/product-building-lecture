"""
FastAPI backend for handwritten digit recognition.
Serves the frontend and handles POST /predict.

Run:
    uvicorn main:app --reload
Then open: http://localhost:8000
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from model import load_or_train_model, preprocess_base64

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend")

ml_model = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    ml_model["clf"] = load_or_train_model()
    yield
    ml_model.clear()


app = FastAPI(title="Digit Recognition API", lifespan=lifespan)


class PredictRequest(BaseModel):
    image: str  # base64-encoded PNG from canvas


class PredictResponse(BaseModel):
    digit: int
    confidence: float
    probabilities: list[float]


@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    flat = preprocess_base64(req.image)
    if flat is None:
        raise HTTPException(status_code=400, detail="Empty canvas — nothing drawn.")

    probas = ml_model["clf"].predict_proba(flat)[0]
    digit = int(probas.argmax())
    return PredictResponse(
        digit=digit,
        confidence=round(float(probas[digit]), 4),
        probabilities=[round(float(p), 4) for p in probas],
    )


# Serve frontend static files
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
