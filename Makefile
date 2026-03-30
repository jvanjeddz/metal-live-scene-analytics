.PHONY: setup ingest-kaggle ingest-setlistfm ingest load-raw dbt-run dbt-test \
       pipeline dashboard docker-up docker-down tf-init tf-plan tf-apply tf-destroy

# ─── Python ──────────────────────────────────────────────────────────────────────

setup:
	uv sync

ingest-kaggle:
	uv run python ingest_kaggle.py

ingest-setlistfm:
	uv run python ingest_setlistfm.py

ingest: ingest-kaggle ingest-setlistfm

load-raw:
	uv run python -m pipeline.load_raw

dbt-run:
	cd dbt_project && uv run dbt run

dbt-test:
	cd dbt_project && uv run dbt test

pipeline:
	uv run python flows/full_pipeline.py

dashboard:
	uv run streamlit run streamlit_app/app.py

# ─── Docker ──────────────────────────────────────────────────────────────────────

docker-up:
	docker compose up --build -d

docker-down:
	docker compose down

# ─── Terraform ───────────────────────────────────────────────────────────────────

tf-init:
	cd terraform && terraform init

tf-plan:
	cd terraform && terraform plan

tf-apply:
	cd terraform && terraform apply

tf-destroy:
	cd terraform && terraform destroy
