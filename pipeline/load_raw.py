"""Load raw CSV files into BigQuery via GCS."""

import os
from pathlib import Path

from google.cloud import bigquery, storage

PROJECT_ID = os.environ["GCP_PROJECT_ID"]
BUCKET_NAME = os.environ["GCS_BUCKET"]

MA_DIR = Path("data/raw/metal_archives")
SFM_DIR = Path("data/raw/setlistfm")

# Table definitions: local_path, bq_table, select/rename SQL (None = keep as-is)
TABLES = [
    {
        "path": MA_DIR / "metal_bands.csv",
        "table": "bands",
        "select": {
            "Band_ID": "band_id",
            "Name": "band_name",
            "Country": "country",
            "Genre": "genre",
            "Status": "status",
        },
    },
    {
        "path": MA_DIR / "all_bands_discography.csv",
        "table": "albums",
        "select": {
            "Album_Name": "album_name",
            "Type": "album_type",
            "Year": "year",
            "Reviews": "reviews",
            "Band_ID": "band_id",
        },
    },
    {
        "path": MA_DIR / "labels_roster.csv",
        "table": "labels",
        "select": {
            "Label_ID": "label_id",
            "Band_ID": "band_id",
            "Name": "label_name",
            "Specialization": "specialization",
            "Status": "status",
            "Country": "country",
        },
    },
    {"path": SFM_DIR / "setlists.csv", "table": "setlists", "select": None},
    {"path": SFM_DIR / "songs.csv", "table": "songs", "select": None},
    {"path": SFM_DIR / "band_mapping.csv", "table": "band_mapping", "select": None},
]


def upload_to_gcs(local_path: Path, gcs_path: str) -> str:
    """Upload a local file to GCS and return the gs:// URI."""
    client = storage.Client(project=PROJECT_ID)
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(gcs_path)
    blob.upload_from_filename(str(local_path))
    uri = f"gs://{BUCKET_NAME}/{gcs_path}"
    print(f"  Uploaded {local_path} → {uri}")
    return uri


def load_gcs_to_bq(gcs_uri: str, table_id: str, select: dict | None):
    """Load a CSV from GCS into a BigQuery table."""
    client = bigquery.Client(project=PROJECT_ID)

    # Load with autodetect — BigQuery reads headers and infers types
    # Force all STRING schema for tables with select map (Metal Archives CSVs
    # have IDs that look numeric but aren't always, e.g. binary-looking band IDs)
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )

    if select:
        # Read actual CSV header to build all-STRING schema
        gcs_path = gcs_uri.replace(f"gs://{BUCKET_NAME}/", "")
        storage_client = storage.Client(project=PROJECT_ID)
        blob = storage_client.bucket(BUCKET_NAME).blob(gcs_path)
        header_line = blob.download_as_text(end=4096).split("\n")[0]
        col_names = [c.strip().replace(" ", "_") for c in header_line.split(",")]
        job_config.schema = [bigquery.SchemaField(name, "STRING") for name in col_names]
    else:
        job_config.autodetect = True

    load_job = client.load_table_from_uri(gcs_uri, table_id, job_config=job_config)
    load_job.result()

    table = client.get_table(table_id)
    print(f"  Loaded {table.num_rows:,} rows → {table_id}")

    # Select and rename columns if needed (Metal Archives CSVs have extra columns)
    if select:
        col_selects = ", ".join(
            f"CAST({old} AS STRING) AS {new}" for old, new in select.items()
        )
        query = f"""
            CREATE OR REPLACE TABLE `{table_id}` AS
            SELECT {col_selects}
            FROM `{table_id}`
        """
        client.query(query).result()
        print(f"  Selected/renamed columns for {table_id}")


def load_raw():
    """Upload CSVs to GCS, then load into BigQuery raw dataset."""
    print(f"Project: {PROJECT_ID} | Bucket: {BUCKET_NAME}")

    for t in TABLES:
        name = t["table"]
        local_path = t["path"]
        table_id = f"{PROJECT_ID}.raw.{name}"

        print(f"\n--- {name} ---")

        # Step 1: Upload to GCS
        gcs_path = f"raw/{local_path.parent.name}/{local_path.name}"
        gcs_uri = upload_to_gcs(local_path, gcs_path)

        # Step 2: Load into BigQuery
        load_gcs_to_bq(gcs_uri, table_id, t["select"])

    print("\nAll raw tables loaded successfully.")


if __name__ == "__main__":
    load_raw()
