# hyuabot-library-updater

A recurring job that scrapes real-time reading room seat availability from Hanyang University library branches and keeps the HYUabot database up to date. Runs every minute as a Kubernetes CronJob.

## Overview

On each run the job:

1. Fetches seat availability for all library branches using aiohttp and BeautifulSoup4.
2. Updates the `reading_room` table with current occupancy data.
3. Sends push notifications via Firebase Cloud Messaging (FCM) when thresholds are crossed.

## Architecture

```
src/
├── main.py              # Entry point; fetches all branch data and sends notifications
├── models.py            # SQLAlchemy ORM models (ReadingRoom)
├── scripts/
│   └── realtime.py      # Fetches real-time seat data and updates the database
└── utils/
    └── database.py      # PostgreSQL engine factory
```

## Requirements

- Python ≥ 3.12
- PostgreSQL
- Google service account JSON with Firebase Cloud Messaging access

## Environment Variables

| Variable             | Description                                   |
|----------------------|-----------------------------------------------|
| `GOOGLE_PROJECT_ID`  | Google Cloud project ID (for FCM)             |
| `POSTGRES_ID`        | PostgreSQL username                           |
| `POSTGRES_PASSWORD`  | PostgreSQL password                           |
| `POSTGRES_HOST`      | PostgreSQL host                               |
| `POSTGRES_PORT`      | PostgreSQL port                               |
| `POSTGRES_DB`        | PostgreSQL database name                      |

A Google service account JSON file must be present in the container (copied at Docker build time from `google-application-credentials.json`).

## Running Locally

```bash
pip install -e .

export GOOGLE_PROJECT_ID=your_project_id
export POSTGRES_ID=postgres
export POSTGRES_PASSWORD=password
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=hyuabot

# Place your service account JSON at the expected path
cp /path/to/service-account.json google-application-credentials.json

cd src && python main.py
```

## Docker

The container exits after a single run — schedule it externally (Kubernetes CronJob every minute).

The service account JSON is copied into the image at build time — ensure `google-application-credentials.json` exists in the repository root before building.

```bash
docker build -t hyuabot-library-updater .

docker run --rm \
  -e GOOGLE_PROJECT_ID=your_project_id \
  -e POSTGRES_ID=postgres \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_HOST=host.docker.internal \
  -e POSTGRES_PORT=5432 \
  -e POSTGRES_DB=hyuabot \
  hyuabot-library-updater
```

## Development

```bash
pip install -e .[lint]       # flake8
pip install -e .[typecheck]  # mypy
pip install -e .[test]       # pytest
```

```bash
python -m flake8 src/ tests/
python -m mypy src/ tests/
python -m pytest -v
```

Tests require a `GOOGLE_APPLICATION_CREDENTIALS` environment variable pointing to a valid service account JSON. Tests run against a PostgreSQL instance at `localhost:25432`.

## CI/CD

| Workflow | Trigger | Jobs |
|---|---|---|
| `code-check.yml` | Push to any branch except `main` | lint, typecheck, test |
| `deploy.yml` | PR merged to `main` (or manual dispatch) | Docker build → push to `localhost:5000` |

CI runners: self-hosted X64 Linux (code checks) · ARM64 Linux (Docker build).

## License

GPLv3
