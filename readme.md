# EasyIntern (Python)

A scrappy, transparent internship search and ranking tool. It pulls postings from ATS sources (Greenhouse, Lever) and optional RSS feeds, stores them in SQLite, and ranks them against a student profile.

## Quickstart

```bash
pip install -r requirements.txt
python -m app.cli scrape --config scrape_config.json
python -m app.cli rank --profile candidate_profile.json --top 50 --export results.csv
uvicorn app.api:app --reload --port 8000
