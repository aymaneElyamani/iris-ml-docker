from typing import Annotated

import redis
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from sklearn.datasets import load_iris
from sklearn.linear_model import LogisticRegression


REDIS_HOST = "base"
REDIS_PORT = 6379
PREDICTION_COUNTER = "predictions"

iris = load_iris()
model = LogisticRegression(max_iter=300, random_state=42)
model.fit(iris.data, iris.target)
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True,
)

app = FastAPI(title="Iris prediction API")


class PredictionRequest(BaseModel):
    features: Annotated[
        list[float],
        Field(min_length=4, max_length=4, description="Sepal and petal measurements"),
    ]


@app.get("/health")
def health() -> dict[str, str]:
    try:
        redis_client.ping()
    except redis.RedisError as error:
        raise HTTPException(status_code=503, detail="Redis is unavailable") from error
    return {"status": "ok"}


@app.post("/predict")
def predict(request: PredictionRequest) -> dict[str, object]:
    prediction = int(model.predict([request.features])[0])

    try:
        count = int(redis_client.incr(PREDICTION_COUNTER))
    except redis.RedisError as error:
        raise HTTPException(status_code=503, detail="Redis is unavailable") from error

    return {
        "prediction": prediction,
        "species": iris.target_names[prediction],
        "count": count,
    }


@app.get("/stats")
def stats() -> dict[str, int]:
    try:
        count = redis_client.get(PREDICTION_COUNTER)
    except redis.RedisError as error:
        raise HTTPException(status_code=503, detail="Redis is unavailable") from error
    return {"predictions": int(count or 0)}
