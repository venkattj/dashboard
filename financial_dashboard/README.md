# Financial Dashboard Web App

This Flask app reads the checked-in `Income.xlsx`, seeds a SQLite store, and renders the dashboard/CRUD UI. The database now lives in `data/dashboard.db` (customizable via `SQLITE_PATH`) so the workbook-backed data persists between restarts.

## Local setup
1. Install dependencies: `pip install -r requirements.txt`
2. (Optional) Set `WORKBOOK_PATH` if you want to seed from another workbook, and `SQLITE_PATH` if you prefer a different SQLite file location.
3. `python app.py` will create/populate the database at `data/dashboard.db` and start the Flask server on `http://localhost:5000`. Reloading via the UI overwrites `WORKBOOK_PATH` so the on-disk database can be refreshed without re-deploying.

## Deploying on Render
1. Keep `render.yaml` committed—Render installs dependencies and runs `gunicorn app:app --bind 0.0.0.0:$PORT` from the `financial_dashboard` directory.
2. If you want the SQLite file outside of `data/dashboard.db`, set `SQLITE_PATH` to a path under the repo (e.g., `data/render_dashboard.db`).
3. Use the dashboard’s "Reload From Workbook" file picker whenever you need to reseed the persistent SQLite file after deploys.
