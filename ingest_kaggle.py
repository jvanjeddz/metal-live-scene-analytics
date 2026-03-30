"""Download Metal Archives dataset from Kaggle.

Authenticates via the KAGGLE_API_TOKEN env var.
"""

from pathlib import Path

from kaggle.api.kaggle_api_extended import KaggleApi

DATASET = "guimacrlh/every-metal-archives-band-october-2024"
OUT_DIR = Path("data/raw/metal_archives")
EXPECTED_FILES = ["metal_bands.csv", "all_bands_discography.csv", "labels_roster.csv"]


def download_metal_archives():
    """Download and extract the Metal Archives Kaggle dataset."""
    if all((OUT_DIR / f).exists() for f in EXPECTED_FILES):
        print(f"Metal Archives data already present in {OUT_DIR}, skipping download.")
        return

    print(f"Downloading {DATASET} → {OUT_DIR}...")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    api = KaggleApi()
    api.authenticate()
    api.dataset_download_files(DATASET, path=str(OUT_DIR), unzip=True)
    print(f"Done. Files: {[f.name for f in sorted(OUT_DIR.iterdir())]}")


if __name__ == "__main__":
    download_metal_archives()
