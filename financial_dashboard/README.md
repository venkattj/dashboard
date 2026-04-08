# Financial Dashboard Web App

This Flask app reads the Income.xlsx workbook, seeds a MySQL database, and renders the dashboard/CRUD UI.

## Local setup
1. Install dependencies: pip install -r requirements.txt
2. Point a local MySQL instance at the credentials defined via environment variables (MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB, MYSQL_PORT).
3. Run python app.py and open http://localhost:5000.

## Deploying on Render
1. Commit ender.yaml so Render picks up the Python web service definition (it installs equirements.txt and runs gunicorn app:app --bind 0.0.0.0:).
2. In the Render dashboard, create a web service from this repo, choose the python environment, and use the generated ender.yaml. Render will install dependencies and use gunicorn to serve the app.
3. Configure the service-level environment variables (MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB, MYSQL_PORT) to point at your Render managed database, and optionally override WORKBOOK_PATH if you store the workbook somewhere else.
4. The workbook in source control (Income.xlsx) will seed the database the first time the service starts.

