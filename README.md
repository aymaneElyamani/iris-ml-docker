# iris-ml-docker

A containerized **Iris** prediction API. The API trains its classifier when it
starts, predicts flower species over HTTP, and stores the number of predictions
in Redis.

## Table of contents

- [How it works](#how-it-works)
- [Project structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Quick start](#quick-start)
- [Results](#results)
- [Dependencies](#dependencies)

## How it works

The Compose application consists of two containers:

1. **api** — exposes `/predict`, `/stats`, and `/health` on port `8000`.
2. **base** — Redis, with append-only persistence in the named `redis-data`
   volume.

The API waits for Redis to pass its healthcheck before starting.

## Project structure

```
iris-ml-docker/
├── src/
│   ├── app.py                       # HTTP prediction API
│   ├── train.py                     # Original training script
│   └── inference.py                 # Original inference script
├── Dockerfile                       # API image
├── docker-compose.yml               # api + Redis orchestration
├── requirements.txt                 # Python dependencies
├── trivy-*-critical.txt             # Trivy scan reports (critical CVEs)
├── .dockerignore
└── .gitignore
```

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose (`docker compose` plugin)
- No local Python installation is required to run the pipeline via Docker.

## Quick start

Validate and start the API:

```bash
docker compose config
docker compose up --build
```

Send predictions from another terminal:

```bash
curl -X POST http://localhost:8000/predict ^
  -H "Content-Type: application/json" ^
  -d "{\"features\":[5.1,3.5,1.4,0.2]}"
curl http://localhost:8000/stats
```

Each successful `/predict` increments the Redis counter.

Stop and restart without deleting volumes:

```bash
docker compose down
docker compose up -d
```

The value returned by `/stats` survives because the named Redis volume is kept.
To remove the volume as well:

```bash
docker compose down -v
```

After `down -v`, Redis starts with an empty counter, so `/stats` returns
`{"predictions":0}` until the next prediction.

## Dependencies

| Package         | Version |
| --------------- | ------- |
| numpy           | 2.2.6   |
| scikit-learn    | 1.7.2   |
| joblib          | 1.5.2 |
| fastapi         | 0.115.6 |
| uvicorn         | 0.34.0 |
| redis           | 5.2.1 |
