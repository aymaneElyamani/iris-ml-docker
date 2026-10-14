# iris-ml-docker

Pipeline de machine learning containerisé qui entraîne un modèle de classification
sur le célèbre jeu de données **Iris**, puis effectue une prédiction à partir de ce
modèle. Le projet illustre deux approches de construction d'images Docker : une version
**naïve** et une version **optimisée** (multi-stage, image `slim`, utilisateur non-root).

## Sommaire

- [Fonctionnement](#fonctionnement)
- [Structure du projet](#structure-du-projet)
- [Prérequis](#prérequis)
- [Démarrage rapide](#démarrage-rapide)
- [Variantes : naïve vs optimisée](#variantes--naïve-vs-optimisée)
- [Sécurité](#sécurité)
- [Exécution sans Docker](#exécution-sans-docker)

## Fonctionnement

Le pipeline se compose de deux conteneurs qui partagent un volume Docker :

1. **trainer** — charge le jeu de données Iris (`sklearn.datasets.load_iris`),
   entraîne une régression logistique, évalue la précision sur un jeu de test
   (20 % des données) et sérialise le modèle dans `/model/iris_model.joblib`.
2. **inference** — récupère le modèle entraîné, puis prédit l'espèce d'une fleur
   pour un échantillon donné, avec les probabilités associées.

Le conteneur `inference` ne démarre qu'après la fin réussie du conteneur `trainer`
(`depends_on: condition: service_completed_successfully`).

## Structure du projet

```
iris-ml-docker/
├── src/
│   ├── train.py                     # Entraînement du modèle
│   └── inference.py                 # Prédiction à partir du modèle
├── Dockerfile.train                 # Image d'entraînement (naïve)
├── Dockerfile.train.optimized       # Image d'entraînement (optimisée)
├── Dockerfile.inference             # Image d'inférence (naïve)
├── Dockerfile.inference.optimized   # Image d'inférence (optimisée)
├── docker-compose.yml               # Orchestration trainer + inference
├── requirements.txt                 # Dépendances Python
├── trivy-*-critical.txt             # Rapports de scan Trivy (CVE critiques)
├── .dockerignore
└── .gitignore
```

## Prérequis

- [Docker](https://docs.docker.com/get-docker/) et Docker Compose (plugin `docker compose`)
- Aucune installation Python locale n'est requise pour exécuter via Docker.

## Démarrage rapide

Lancez le pipeline complet (entraînement puis inférence) :

```bash
docker compose up --build
```

Ce que vous verrez dans les logs :

- côté `trainer` : la précision du modèle, par exemple `Accuracy: 0.9667`, puis
  `Model saved to: /model/iris_model.joblib` ;
- côté `inference` : l'échantillon d'entrée, la classe prédite, le nom de la fleur
  et les probabilités par classe.

Pour réinitialiser complètement (supprimer le volume du modèle) :

```bash
docker compose down -v
```

### Exécuter les étapes séparément

```bash
# Entraînement
docker build -f Dockerfile.train.optimized -t iris-train:optimized .
docker run --rm -v iris-model:/model iris-train:optimized

# Inférence (le volume contient déjà le modèle)
docker build -f Dockerfile.inference.optimized -t iris-inference:optimized .
docker run --rm -v iris-model:/model iris-inference:optimized
```

## Variantes : naïve vs optimisée

Le projet fournit deux implémentations de chaque image afin de comparer les bonnes
pratiques de construction Docker.

| Critère               | Version naïve (`Dockerfile.train`, `Dockerfile.inference`) | Version optimisée (`*.optimized`) |
| --------------------- | ---------------------------------------------------------- | --------------------------------- |
| Image de base         | `python:3.12` (complète)                                   | `python:3.12-slim`                |
| Construction          | Mono-stage                                                 | Multi-stage (builder + runtime)   |
| Dépendances           | Installées dans le système                                 | Installées dans un virtualenv `/opt/venv` |
| Utilisateur           | `root`                                                     | `appuser` (non-root)             |
| Copie du code         | `COPY . .` (tout le contexte)                              | Uniquement le script nécessaire   |
| Taille / surface d'attaque | Plus grande                                          | Réduite                           |

Points clés de la version optimisée :

- **Multi-stage build** : les outils de compilation restent dans l'étape `builder`,
  seul le virtualenv est copié dans l'image finale.
- **Image `slim`** : moins de paquets système, donc une surface d'attaque réduite.
- **Utilisateur non-root** : l'application s'exécute avec `appuser`.
- **Copie ciblée** : seul le script requis est copié, pas l'intégralité du dépôt.

Le `docker-compose.yml` utilise par défaut les Dockerfiles optimisés.

## Sécurité

Le dossier contient des rapports générés par [Trivy](https://github.com/aquasecurity/trivy).
Les fichiers `*-critical.txt` ne listent que les vulnérabilités **critiques**, tandis
que les fichiers `*-train.txt` couvrent **toutes les sévérités**.

| Rapport                          | Image                    | Critiques | Total (toutes sévérités) |
| -------------------------------- | ------------------------ | --------- | ------------------------ |
| `trivy-naive-critical.txt`       | `iris-train:naive`       | 16        | —                        |
| `trivy-naive-train.txt`          | `iris-train:naive`       | 16        | 305 (dont 289 HIGH)      |
| `trivy-optimized-critical.txt`   | `iris-train:optimized`   | 0         | —                        |
| `trivy-optimized-train.txt`      | `iris-train:optimized`   | 0         | 48 (toutes HIGH)         |

La version optimisée élimine la totalité des vulnérabilités critiques présentes
dans la version naïve, principalement grâce à l'image `slim` et à la réduction
des paquets installés.

Pour reproduire un scan :

```bash
trivy image --severity CRITICAL iris-train:naive
trivy image --severity CRITICAL iris-train:optimized
```

## Exécution sans Docker

Pour tester les scripts directement (Python 3.12 recommandé), adaptez le chemin
`/model` défini dans `src/train.py` et `src/inference.py` :

```bash
pip install -r requirements.txt
mkdir -p /model  # ou ajustez MODEL_DIR / MODEL_PATH dans les scripts
python src/train.py
python src/inference.py
```

## Dépendances

| Paquet          | Version |
| --------------- | ------- |
| numpy           | 2.2.6   |
| scikit-learn    | 1.7.2   |
| joblib          | 1.5.2   |
