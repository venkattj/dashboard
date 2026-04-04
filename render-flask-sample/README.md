# Render Flask Sample

This folder contains a minimal Flask UI + API designed to illustrate how to deploy a Python web service on Render.

## Features
- A single HTML dashboard that calls two backend endpoints (`/api/quote` and `/api/stats`).
- Simple in-memory payloads so there is no database dependency.
- Render-friendly entrypoint (`app.py`) that can be scaled with Gunicorn.

## Local setup
Use the provided `run-local.bat` when you want the full setup/run sequence in one command.

1. Run `run-local.bat` to create/activate the `.venv`, install dependencies, and start the Flask app.
2. Open `http://localhost:5000` when the console reports `Running on http://127.0.0.1:5000`.

## APIs
- `/api/quote` returns a motivational quote, a fixed author, and a UTC timestamp.
- `/api/stats` returns simulated metrics (active users, conversion rate, region totals) plus a timestamp.

The UI uses JavaScript `fetch` calls to display both data sources and offers refresh buttons for each.

## Deploying on Render
- Render runs the `buildCommand` before each deploy and the `startCommand` after the build completes, so this sample keeps those commands simple (`pip install -r requirements.txt` and `gunicorn app:app`).
- The included `render.yaml` declares one Python web service using the Free instance type; Render will honor the `buildCommand`, `startCommand`, and environment variables defined there.
- Render automatically exposes the service via an `onrender.com` URL that you can pull from the Dashboard.

Adjust `render.yaml` if you need custom environment variables, secrets, or a different instance type.
