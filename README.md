# Iris ML Docker

Containerized HTTP API for predicting Iris flowers with Docker and Docker
Compose. The API trains a logistic regression model at startup, exposes
predictions through FastAPI, and uses Redis to count successful predictions.

## Table of contents

- [How it works](#how-it-works)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Quick start](#quick-start)
- [HTTP API](#http-api)
- [Separate training pipeline](#separate-training-pipeline)
- [Project structure](#project-structure)
- [Dependencies](#dependencies)

## How it works

The main deployment consists of two services:

| Service | Role |
| --- | --- |
| `api` | Trains the Iris model in memory and exposes the API on port `8000`. |
| `base` | Redis `7-alpine`, used to store the prediction counter. |

The API connects to Redis through the `base` DNS name. The `api` service waits
until the Redis healthcheck succeeds before starting. Redis runs with AOF
persistence, and its data is stored in the Docker volume named `redis-data`.

> **Note:** The model used by `src/app.py` is trained when the container starts
> and is not loaded from `/model`. The `train.py` and `inference.py` scripts
> belong to a separate pipeline, described below.

## Architecture

```text
HTTP client
    │
    ▼
api (FastAPI + scikit-learn) :8000
    │
    ▼
base (Redis 7) :6379
    │
    ▼
redis-data volume
```

## Prerequisites

- [Docker Desktop](https://docs.docker.com/get-docker/) with the
  `docker compose` plugin.
- No local Python environment is required to run `docker-compose.yml`.

Verify the installation:

```bash
docker --version
docker compose version
```

## Quick start

From the repository root:

```bash
docker compose config
docker compose up --build
```

The API is then available at
[`http://localhost:8000`](http://localhost:8000). To start it in the
background, use `docker compose up --build -d`.

### Check the service status

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{"status":"ok"}
```

### Make a prediction

The four values correspond to the following Iris measurements, in this order:
`sepal length`, `sepal width`, `petal length`, and `petal width`, in
centimeters. The request must contain exactly four numbers.

Linux/macOS:

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"features":[5.1,3.5,1.4,0.2]}'
```

PowerShell:

```powershell
curl.exe -X POST http://localhost:8000/predict `
  -H "Content-Type: application/json" `
  -d '{"features":[5.1,3.5,1.4,0.2]}'
```

Example response:

```json
{"prediction":0,"species":"setosa","count":1}
```

Each successful prediction atomically increments the Redis `predictions` key.

### View statistics

```bash
curl http://localhost:8000/stats
```

Response when the counter is `1`:

```json
{"predictions":1}
```

The interactive FastAPI documentation is available at
[`http://localhost:8000/docs`](http://localhost:8000/docs), and the OpenAPI
schema is available at
[`http://localhost:8000/openapi.json`](http://localhost:8000/openapi.json).

### Stop the application

Stop the containers while keeping the Redis data:

```bash
docker compose down
```

Also remove the persistent counter:

```bash
docker compose down -v
```

After `down -v`, the counter starts again at `0`.

## Separate training pipeline

`src/train.py` trains the same type of model and writes the
`/model/iris_model.joblib` artifact. `src/inference.py` then loads this
artifact and performs a demonstration prediction.

The related Dockerfiles are:

- `Dockerfile.train`: simple training container;
- `Dockerfile.inference`: simple inference container;
- `Dockerfile.train.optimized` and `Dockerfile.inference.optimized`:
  multi-stage images based on `python:3.12-slim`, running as a non-root user.

Build and run this pipeline with a local `model` volume:

```bash
docker build -f Dockerfile.train.optimized -t iris-train .
docker run --rm -v "${PWD}/model:/model" iris-train

docker build -f Dockerfile.inference.optimized -t iris-inference .
docker run --rm -v "${PWD}/model:/model" iris-inference
```

In PowerShell, replace `${PWD}` with `${PWD.Path}` if necessary:

```powershell
docker run --rm -v "${PWD.Path}\model:/model" iris-train
docker run --rm -v "${PWD.Path}\model:/model" iris-inference
```

The `model/` directory is ignored by Git and is created locally by the
training container.

## Project structure

```text
iris-ml-docker/
├── src/
│   ├── app.py                    # FastAPI API and startup-trained model
│   ├── train.py                  # Training to /model
│   └── inference.py              # Inference from /model
├── Dockerfile                    # Image used by docker-compose.yml
├── Dockerfile.train              # Simple training image
├── Dockerfile.inference          # Simple inference image
├── Dockerfile.train.optimized    # Optimized training image
├── Dockerfile.inference.optimized # Optimized inference image
├── docker-compose.yml             # API + Redis orchestration
├── requirements.txt               # Pinned Python dependencies
├── images/                        # Report illustrations
├── rapport.tex                    # Project report in LaTeX
└── .dockerignore
```

The `trivy-*.txt` files contain Trivy scan reports generated for the training
images.

## Dependencies

Versions are pinned in `requirements.txt`:

| Package | Version |
| --- | --- |
| numpy | 2.2.6 |
| scikit-learn | 1.7.2 |
| joblib | 1.5.2 |
| fastapi | 0.115.6 |
| uvicorn | 0.34.0 |
| redis | 5.2.1 |

## License

No open-source license is currently declared in this repository.
