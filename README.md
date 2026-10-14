# iris-ml-docker

A containerized machine learning pipeline that trains a classification model on the
famous **Iris** dataset, then makes a prediction using that model. The project
illustrates two approaches to building Docker images: a **naive** version and an
**optimized** version (multi-stage, `slim` base image, non-root user).

## Table of contents

- [How it works](#how-it-works)
- [Project structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Quick start](#quick-start)
- [Results](#results)
- [Variants: naive vs optimized](#variants-naive-vs-optimized)
- [Security](#security)
- [Running without Docker](#running-without-docker)

## How it works

The pipeline consists of two containers that share a Docker volume:

1. **trainer** — loads the Iris dataset (`sklearn.datasets.load_iris`), trains a
   logistic regression, evaluates accuracy on a test set (20% of the data) and
   serializes the model to `/model/iris_model.joblib`.
2. **inference** — loads the trained model, then predicts the species of a flower
   for a given sample, along with the associated probabilities.

The `inference` container only starts after the `trainer` container finishes
successfully (`depends_on: condition: service_completed_successfully`).

## Project structure

```
iris-ml-docker/
├── src/
│   ├── train.py                     # Model training
│   └── inference.py                 # Prediction from the model
├── Dockerfile.train                 # Training image (naive)
├── Dockerfile.train.optimized       # Training image (optimized)
├── Dockerfile.inference             # Inference image (naive)
├── Dockerfile.inference.optimized   # Inference image (optimized)
├── docker-compose.yml               # trainer + inference orchestration
├── requirements.txt                 # Python dependencies
├── trivy-*-critical.txt             # Trivy scan reports (critical CVEs)
├── .dockerignore
└── .gitignore
```

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose (`docker compose` plugin)
- No local Python installation is required to run the pipeline via Docker.

## Quick start

Run the full pipeline (training, then inference):

```bash
docker compose up --build
```

What you will see in the logs:

- on the `trainer` side: the model accuracy, for example `Accuracy: 0.9667`, then
  `Model saved to: /model/iris_model.joblib`;
- on the `inference` side: the input sample, the predicted class, the flower name
  and the per-class probabilities.

To reset everything (and delete the model volume):

```bash
docker compose down -v
```

### Running the steps separately

```bash
# Training
docker build -f Dockerfile.train.optimized -t iris-train:optimized .
docker run --rm -v iris-model:/model iris-train:optimized

# Inference (the volume already contains the model)
docker build -f Dockerfile.inference.optimized -t iris-inference:optimized .
docker run --rm -v iris-model:/model iris-inference:optimized
```

## Results

Below is the output of a complete `docker compose up --build` run.

**`trainer` container:**

```
Loading Iris dataset...
Training model...
Accuracy: 0.9667
Model saved to: /model/iris_model.joblib
```

**`inference` container:**

```
Loading trained model...
Input: [5.1, 3.5, 1.4, 0.2]
Predicted class ID: 0
Predicted flower: setosa
Probabilities: [9.78399914e-01 2.16000313e-02 5.50870783e-08]
```

Both containers exit with code `0`, and both images (`iris-train:optimized` and
`iris-inference:optimized`) are built locally. The trained model is stored in the
`iris-model` Docker volume and is reused by the inference step.

> **Tip:** if Docker Desktop becomes unresponsive and `docker` returns a
> `500 Internal Server Error`, restart Docker Desktop before running the pipeline again.

## Variants: naive vs optimized

The project provides two implementations of each image in order to compare Docker
build best practices.

| Criterion               | Naive version (`Dockerfile.train`, `Dockerfile.inference`) | Optimized version (`*.optimized`)   |
| ----------------------- | ---------------------------------------------------------- | ----------------------------------- |
| Base image              | `python:3.12` (full)                                       | `python:3.12-slim`                  |
| Build                   | Single-stage                                               | Multi-stage (builder + runtime)     |
| Dependencies            | Installed system-wide                                      | Installed in a `/opt/venv` virtualenv |
| User                    | `root`                                                     | `appuser` (non-root)                |
| Code copy               | `COPY . .` (whole context)                                 | Only the required script            |
| Size / attack surface   | Larger                                                     | Smaller                             |

Key points of the optimized version:

- **Multi-stage build**: compilation tools stay in the `builder` stage, only the
  virtualenv is copied into the final image.
- **`slim` image**: fewer system packages, hence a smaller attack surface.
- **Non-root user**: the application runs as `appuser`.
- **Targeted copy**: only the required script is copied, not the entire repository.

The `docker-compose.yml` uses the optimized Dockerfiles by default.

## Security

The folder contains reports generated by [Trivy](https://github.com/aquasecurity/trivy).
The `*-critical.txt` files list only **critical** vulnerabilities, while the
`*-train.txt` files cover **all severities**.

| Report                           | Image                    | Critical | Total (all severities)   |
| -------------------------------- | ------------------------ | -------- | ------------------------ |
| `trivy-naive-critical.txt`       | `iris-train:naive`       | 16       | —                        |
| `trivy-naive-train.txt`          | `iris-train:naive`       | 16       | 305 (including 289 HIGH) |
| `trivy-optimized-critical.txt`   | `iris-train:optimized`   | 0        | —                        |
| `trivy-optimized-train.txt`      | `iris-train:optimized`   | 0        | 48 (all HIGH)            |

The optimized version eliminates all critical vulnerabilities present in the naive
version, mainly thanks to the `slim` image and the reduced number of installed
packages.

To reproduce a scan:

```bash
trivy image --severity CRITICAL iris-train:naive
trivy image --severity CRITICAL iris-train:optimized
```

## Running without Docker

To test the scripts directly (Python 3.12 recommended), adjust the `/model` path
defined in `src/train.py` and `src/inference.py`:

```bash
pip install -r requirements.txt
mkdir -p /model  # or adjust MODEL_DIR / MODEL_PATH in the scripts
python src/train.py
python src/inference.py
```

## Dependencies

| Package         | Version |
| --------------- | ------- |
| numpy           | 2.2.6   |
| scikit-learn    | 1.7.2   |
| joblib          | 1.5.2   |
