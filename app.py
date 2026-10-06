"""Streamlit interactive dashboard for web scraping pipeline exploration."""

import json
from pathlib import Path
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Multi-Source Web Scraping Pipeline",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Multi-Source Web Scraping & Consolidation Pipeline")
st.caption("Realisieren Technologies Technical Assessment • Books to Scrape & Quotes to Scrape")

csv_path = Path("output/final_dataset.csv")
summary_path = Path("output/summary_report.json")

if not csv_path.exists() or not summary_path.exists():
    st.error("Output files missing. Please run `python main.py` first.")
    st.stop()

with open(summary_path, "r", encoding="utf-8") as f:
    summary = json.load(f)

df = pd.read_csv(csv_path)

# Metrics Cards
m1, m2, m3, m4, m5, m6 = st.columns(6)
m1.metric("Raw Scraped", summary["total_raw_collected"])
m2.metric("Books Scraped", summary["collected_per_source"]["Books to Scrape"])
m3.metric("Quotes Scraped", summary["collected_per_source"]["Quotes to Scrape"])
m4.metric("Validation Rejected", summary["validation_summary"]["rejected_records"])
m5.metric("Duplicates Detected", summary["duplicate_summary"]["duplicates_detected"])
m6.metric("Final Records", summary["final_record_count"])

st.markdown("---")

# Filters & Controls
col_source, col_search = st.columns([1, 2])
with col_source:
    source_choice = st.selectbox("Filter Source", ["All Sources", "Books to Scrape", "Quotes to Scrape"])
with col_search:
    search_query = st.text_input("Search (Title, Author, Tags)", "")

filtered_df = df.copy()
if source_choice != "All Sources":
    filtered_df = filtered_df[filtered_df["source"] == source_choice]

if search_query:
    q = search_query.lower()
    mask = (
        filtered_df["name_or_title"].fillna("").str.lower().str.contains(q)
        | filtered_df["author"].fillna("").str.lower().str.contains(q)
        | filtered_df["tags"].fillna("").str.lower().str.contains(q)
    )
    filtered_df = filtered_df[mask]

st.subheader(f"Dataset View ({len(filtered_df)} records)")
st.dataframe(filtered_df, use_container_width=True)

# Technical Details
with st.expander("🔍 View Execution Summary JSON"):
    st.json(summary)
