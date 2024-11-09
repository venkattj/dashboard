from flask import Blueprint, jsonify
from flask_mysqldb import MySQL
import subprocess

mysql = MySQL()
bp = Blueprint('db_routes', __name__)

# MySQL service control functions
def stop_mysql_service():
    try:
        result = subprocess.run(['net', 'stop', 'MySQL80'], capture_output=True, text=True, check=True)
        return jsonify(result.stdout) , 200
    except subprocess.CalledProcessError as e:
        return jsonify(f"Error stopping MySQL service: {e.stderr}") , 500

def start_mysql_service():
    try:
        result = subprocess.run(['net', 'start', 'MySQL80'], capture_output=True, text=True, check=True)
        return jsonify(result.stdout) , 200
    except subprocess.CalledProcessError as e:
        return jsonify(f"Error starting MySQL service: {e.stderr}"), 500

@bp.route('/mysql/start', methods=['GET'])
def start_service():
    return start_mysql_service()

@bp.route('/mysql/stop', methods=['GET'])
def stop_service():
    return stop_mysql_service()

@bp.route('/health', methods=['GET'])
def health_check():
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        return jsonify({"status": "healthy", "database": "connected"}), 200
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500
