# NBA Player Shooting Comparison

Interactive Streamlit dashboard for comparing NBA players across seasons using shot-location data, shooting efficiency, and season-level performance metrics.

## Features

* Player-to-player season comparison
* Interactive shooting zone heatmaps
* Shot location visualizations
* Season-level performance metrics (PPG, RPG, APG, shooting splits)

## Tech Stack

Python • NBA API • Snowflake • dbt • Streamlit • Altair • Matplotlib

## Architecture

NBA API → Snowflake → dbt Models → Streamlit Dashboard

## Running Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Demo Link

https://nba-shots-analyzer-demo-9.streamlit.app/

## Notes

The original project used Snowflake and dbt for data warehousing and transformations. The public demo utilizes exported CSV mart tables to enable deployment without requiring Snowflake credentials.

