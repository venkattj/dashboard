# Financial Dashboard Web App

This Flask app reads the checked-in `Income.xlsx`, seeds an in-memory SQLite store, and renders the dashboard/CRUD UI. No external database is required for the app to run; every deploy starts with a fresh in-memory schema that is immediately populated from the workbook file.

## Local setup
1. Install dependencies: `pip install -r requirements.txt`
2. Adjust `WORKBOOK_PATH` via environment variable if you want to point at another workbook (the default is the repository's `Income.xlsx`).
3. `python app.py` will seed the in-memory store and start the Flask server on `http://localhost:5000`.

## Deploying on Render
1. Commit `render.yaml` so Render uses the provided web service definition (`pip install -r requirements.txt` + `gunicorn app:app --bind 0.0.0.0:$PORT`).
2. Choose the `financial_dashboard` root directory in Render so it runs commands from the right folder.
3. If you want to seed from a workbook other than the checked-in `Income.xlsx`, provide a `WORKBOOK_PATH` environment variable pointing to that file within the Render workspace.
4. Every deploy rebuilds the same data because the in-memory database is seeded from the workbook on startup; to refresh, use the "Reload From Workbook" file picker on the dashboard.
