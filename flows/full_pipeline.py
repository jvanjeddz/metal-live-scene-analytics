"""Prefect flow: full Metal Analytics pipeline."""

import subprocess
import sys
from pathlib import Path

from prefect import flow, task

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DBT_DIR = PROJECT_ROOT / "dbt_project"


@task(name="download-kaggle-data", log_prints=True)
def download_kaggle_data():
    """Download Metal Archives dataset from Kaggle."""
    sys.path.insert(0, str(PROJECT_ROOT))
    from ingest_kaggle import download_metal_archives

    download_metal_archives()


@task(name="ingest-setlistfm", log_prints=True)
def ingest_setlistfm():
    """Fetch setlist data from Setlist.fm API."""
    sys.path.insert(0, str(PROJECT_ROOT))
    from ingest_setlistfm import main

    main()


@task(name="load-raw-data", log_prints=True)
def load_raw_data():
    """Upload CSVs to GCS and load into BigQuery raw dataset."""
    sys.path.insert(0, str(PROJECT_ROOT))
    from pipeline.load_raw import load_raw

    load_raw()


@task(name="dbt-run", log_prints=True)
def dbt_run():
    """Run dbt models (staging + marts)."""
    result = subprocess.run(
        ["uv", "run", "dbt", "run"],
        cwd=DBT_DIR,
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)
        raise RuntimeError("dbt run failed")


@task(name="dbt-test", log_prints=True)
def dbt_test():
    """Run dbt tests."""
    result = subprocess.run(
        ["uv", "run", "dbt", "test"],
        cwd=DBT_DIR,
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)
        raise RuntimeError("dbt test failed")


@flow(name="metal-analytics-pipeline", log_prints=True)
def full_pipeline():
    """End-to-end pipeline: ingest → load raw → dbt run → dbt test."""
    download_kaggle_data()
    ingest_setlistfm()
    load_raw_data()
    dbt_run()
    dbt_test()
    print("Pipeline complete!")


if __name__ == "__main__":
    full_pipeline()
