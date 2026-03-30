"""BigQuery connection helper for Streamlit."""

import os

import streamlit as st
from google.cloud import bigquery


@st.cache_resource
def get_client():
    return bigquery.Client(project=os.environ["GCP_PROJECT_ID"])


@st.cache_data(ttl=600)
def query(sql: str):
    return get_client().query(sql).to_dataframe()
