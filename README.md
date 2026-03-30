# Metal Live Scene Analytics

**How does the metal music live performance landscape relate to recorded music reception?**

This project links [Metal Archives](https://www.metal-archives.com/) data (the canonical database of metal bands, albums, and reviews) with [Setlist.fm](https://www.setlist.fm/) data (the canonical database of concert setlists) to reveal patterns in touring intensity, genre evolution, geographic distribution, and most-performed songs.

## Architecture

```
[Kaggle CSV] ──→ GCS (raw/) ──→ BigQuery (raw dataset)
                                       │
[Setlist.fm API] ──→ GCS (raw/) ──→    │
                                       ▼
                                BigQuery (raw)
                                       │
                              Prefect orchestration
                                       │
                                 dbt run + test
                                       │
                          BigQuery (staging → marts)
                                       │
                          Streamlit + Plotly Dashboard
```

### Tech Stack

| Component | Tool | Justification |
|-----------|------|---------------|
| Cloud | GCP | BigQuery free tier |
| IaC | Terraform | Provisions GCP project, GCS bucket, BigQuery datasets, service account, IAM |
| Data Lake | GCS | Raw CSVs staged before BigQuery load |
| Warehouse | BigQuery | Serverless, 1TB free queries/month |
| Orchestration | Prefect | Lightweight, native Python, built-in retries |
| Transformations | dbt | SQL-native, fits the ~200MB data volume |
| Dashboard | Streamlit + Plotly | Interactive, 10 tiles across 8 pages |

## Data Sources

| Source | Type | Size |
|--------|------|------|
| [Metal Archives (Kaggle dump)](https://www.kaggle.com/datasets/guimacrlh/every-metal-archives-band-october-2024) | Batch CSV | 183K bands, 637K albums |
| [Setlist.fm API](https://api.setlist.fm/) | REST API (2 req/sec) | ~6.8K setlists, ~75K songs (top 50 bands by review count) |

## Data Warehouse Schema

### Partitioning & Clustering

| Table | Partition | Cluster | Justification |
|-------|-----------|---------|---------------|
| `fct_concerts` | `event_date` (monthly) | `primary_subgenre`, `country_code` | Temporal queries benefit from partition pruning; categorical queries benefit from clustering |
| `dim_bands` | None (small) | `country`, `primary_subgenre` | Genre/country lookups |
| `dim_venues` | None (small) | `country_code` | Geographic grouping |

### dbt Models

**Staging (6 views):** `stg_bands`, `stg_albums`, `stg_setlists`, `stg_songs`, `stg_band_mapping`, `stg_labels` — type casting, deduplication, genre parsing, review parsing.

**Marts (13 tables):** `fct_concerts`, `dim_bands`, `dim_venues`, plus 10 aggregation tables powering the dashboard tiles.

**Tests:** 16 tests (unique + not_null on all primary keys).

## Dashboard

10 tiles across 8 pages:

| Page | Tiles |
|------|-------|
| Touring Analysis | Genre touring intensity, rating vs touring correlation |
| Temporal Trends | Concerts over time, subgenre share over time (with "Other" bucket) |
| Geographic | Concert heatmap by country |
| Most-Played Songs | Top performed songs across all artists |
| Review Scores | Box plot distribution of review scores by subgenre |
| Seasonality | Monthly concert distribution |
| Country-Genre | Location quotient analysis, country comparison, genre popularity by country |
| Genre Lifecycle | New bands per year by subgenre, cumulative growth curves |

## Reproducing This Project

### Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Python | 3.13+ | [python.org](https://www.python.org/) |
| uv | latest | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Terraform | 1.0+ | [terraform.io/downloads](https://developer.hashicorp.com/terraform/downloads) |
| gcloud CLI | latest | [cloud.google.com/sdk](https://cloud.google.com/sdk/docs/install) |
| GCP account | free trial OK | [cloud.google.com/free](https://cloud.google.com/free) |

You also need:
- A **GCP billing account** (the free trial $300 credit is sufficient)
- A **Kaggle API token** (`KAGGLE_API_TOKEN`) — get it from [kaggle.com/settings](https://www.kaggle.com/settings) under "API"
- A **Setlist.fm API key** (free at [setlist.fm/settings/api](https://www.setlist.fm/settings/api))

### Step 1: Clone and install dependencies

```bash
git clone https://github.com/jvanjeddz/metal-live-scene-analytics.git
cd metal-live-scene-analytics
uv sync
```

### Step 2: Authenticate with GCP

```bash
# Log in with your Google account (opens browser)
gcloud auth application-default login
```

This is needed for Terraform to create the GCP project. After Terraform runs, the pipeline uses a service account key instead.

### Step 3: Provision cloud infrastructure with Terraform

```bash
# Create your terraform.tfvars from the example
cp terraform/terraform.tfvars.example terraform/terraform.tfvars
```

Edit `terraform/terraform.tfvars` with your values:

```hcl
project_id      = "metal-live-scene-analytics"   # must be globally unique
billing_account = "XXXXXX-XXXXXX-XXXXXX"          # from GCP Console → Billing
region          = "us-central1"
```

To find your billing account ID: GCP Console → Billing → Billing account ID.

```bash
make tf-init
make tf-apply
# Type "yes" when prompted
```

This creates:
- A new GCP project
- A GCS bucket (`<project-id>-data-lake`)
- 3 BigQuery datasets (`raw`, `staging`, `marts`)
- A service account with BigQuery Admin + Storage Admin roles
- A JSON key file at `terraform/keys/sa-key.json`

### Step 4: Set environment variables

```bash
cp .env.example .env
```

Edit `.env` with your actual values:

```bash
export KAGGLE_API_TOKEN=your_kaggle_api_token
export SETLISTFM_API_KEY=your_setlistfm_api_key
export GCP_PROJECT_ID=your-new-gcp-project-id
export GCS_BUCKET=your-new-gcp-bucket
export GOOGLE_APPLICATION_CREDENTIALS=/full/path/to/terraform/keys/sa-key.json
```

**Important:** `GOOGLE_APPLICATION_CREDENTIALS` must be an absolute path.

Then load them into your shell:

```bash
source .env
```

### Step 5: Run the pipeline

```bash
make pipeline
```

This runs the Prefect-orchestrated flow:
1. **ingest_kaggle** — downloads the Metal Archives dataset from Kaggle (skips if already present)
2. **ingest_setlistfm** — fetches setlist data for the top 50 bands from the Setlist.fm API (checkpointed, resumable)
3. **load_raw** — uploads CSVs to GCS, then loads into BigQuery `raw` dataset
4. **dbt run** — builds 6 staging views + 13 mart tables in BigQuery
5. **dbt test** — runs 16 unique/not_null tests on primary keys

Expected output: `PASS=16 WARN=0 ERROR=0`

You can also run ingestion separately: `make ingest-kaggle`, `make ingest-setlistfm`, or `make ingest` (both).

### Step 6: Launch the dashboard

```bash
make dashboard
```

Open [http://localhost:8501](http://localhost:8501) in your browser. Use the sidebar to navigate between the 8 analysis pages.

### Alternative: Run everything with Docker

```bash
# Make sure .env is configured (steps 3-4 above)
docker compose up --build
# Pipeline (ingest + load + dbt) runs first, then dashboard starts at http://localhost:8501
```

### Teardown

To avoid charges after the GCP free trial expires:

```bash
make tf-destroy
# Type "yes" when prompted — this deletes the entire GCP project and all resources
```

## Project Structure

```
metal-live-scene-analytics/
  terraform/                 # IaC: GCP project, GCS, BigQuery, IAM
    main.tf
    variables.tf
    outputs.tf
  pipeline/
    load_raw.py              # CSV → GCS → BigQuery loader
  ingest_kaggle.py           # Kaggle dataset download (Metal Archives)
  ingest_setlistfm.py        # Setlist.fm API ingestion (checkpointed)
  flows/
    full_pipeline.py          # Prefect orchestration
  dbt_project/
    models/
      staging/               # 6 cleaning/parsing views
      marts/                 # 3 dim/fact + 10 aggregation tables
    macros/                  # parse_subgenre, parse_reviews, touring_bucket
  streamlit_app/
    app.py                   # Main page + metrics
    pages/                   # 8 analysis pages
    utils/
      db.py                  # BigQuery connection
      charts.py              # Plotly theme
  Dockerfile
  docker-compose.yml
  Makefile
  pyproject.toml
  .env.example
```

## License

This project uses data from Metal Archives and Setlist.fm for educational purposes.
