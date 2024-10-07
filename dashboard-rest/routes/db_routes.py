from flask import Blueprint, jsonify
from flask_mysqldb import MySQL
import subprocess

mysql = MySQL()
bp = Blueprint('db_routes', __name__)

# MySQL service control functions
def stop_mysql_service():
    try:
        result = subprocess.run(['net', 'stop', 'MySQL80'], capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error stopping MySQL service: {e.stderr}"

def start_mysql_service():
    try:
        result = subprocess.run(['net', 'start', 'MySQL80'], capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error starting MySQL service: {e.stderr}"

@bp.route('/mysql/start', methods=['GET'])
def start_service():
    output = start_mysql_service()
    return jsonify({"message": output})

@bp.route('/mysql/stop', methods=['GET'])
def stop_service():
    output = stop_mysql_service()
    return jsonify({"message": output})

@bp.route('/health', methods=['GET'])
def health_check():
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        return jsonify({"status": "healthy", "database": "connected"}), 200
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500
