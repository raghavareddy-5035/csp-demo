# StudyPulse
Student performance predictor: Flask + SQLite + scikit-learn + pandas + Chart.js + optional Claude tips.

## Run locally
    pip install -r requirements.txt
    python model.py        # trains model
    python app.py          # http://127.0.0.1:5000

## Deploy (Render, free tier)
1. Push this folder to GitHub.
2. Render -> New -> Blueprint -> pick the repo (uses render.yaml + Dockerfile).
3. Optional: set ANTHROPIC_API_KEY for AI-written tips.
Note: SQLite resets on free-tier redeploys; for production use Postgres (set up via a managed DB).
