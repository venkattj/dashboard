# routes/ui_routes.py
from flask import Blueprint, send_from_directory

bp = Blueprint('ui_routes', __name__, static_folder='../../dashboard-app/build')

@bp.route('/')
def serve():
    return send_from_directory(bp.static_folder, 'index.html')

@bp.route('/<path:path>')
def serve_static(path):
    try:
        return send_from_directory(bp.static_folder, path)
    except:
        return send_from_directory(bp.static_folder, 'index.html')
