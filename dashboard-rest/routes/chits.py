from flask import Blueprint, request, jsonify
from flask_mysqldb import MySQL

bp = Blueprint('chits', __name__)
mysql = MySQL()

@bp.route('/api/chits', methods=['POST'])
def create_chit():
    data = request.get_json()
    cur = mysql.connection.cursor()
    if not (data.get('emi')):
        data['emi'] = 0
    cur.execute("INSERT INTO chits(organisation, value, duration, emi, maturity, started) VALUES(%s, %s, %s, %s, %s, %s)",
                (data['organisation'], data['value'], data['duration'], data.get('emi'), data['maturity'], data['started']))
    chit_id = cur.lastrowid
    mysql.connection.commit()
    cur.close()
    return jsonify({'message': 'Chit created successfully', 'chit_id': chit_id}), 201

# Read all chits
@bp.route('/api/chits', methods=['GET'])
def get_chits():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM chits where sno not in (select chit_id from variable_chits);")
    results = cur.fetchall()
    chits = []
    for row in results:
        chits.append({
            'sno': row[0],
            'organisation': row[1],
            'value': row[2],
            'duration': row[3],
            'emi': row[4],
            'maturity': row[5].strftime('%Y-%m-%d'),  # Format date
            'started': row[6].strftime('%Y-%m-%d')   # Format date
        })
    cur.close()
    return jsonify(chits), 200

# Read a specific chit by SNO
@bp.route('/api/chits/<int:sno>', methods=['GET'])
def get_chit(sno):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM chits WHERE sno = %s", (sno,))
    row = cur.fetchone()
    cur.close()
    if row:
        chit = {
            'sno': row[0],
            'organisation': row[1],
            'value': row[2],
            'duration': row[3],
            'emi': row[4],
            'maturity': row[5].strftime('%Y-%m-%d'),  # Format date
            'started': row[6].strftime('%Y-%m-%d')   # Format date
        }
        return jsonify(chit), 200
    else:
        return jsonify({'message': 'Chit not found'}), 404

# Update a chit
@bp.route('/api/chits/<int:sno>', methods=['PUT'])
def update_chit(sno):
    data = request.get_json()
    cur = mysql.connection.cursor()
    cur.execute("UPDATE chits SET organisation = %s, value = %s, duration = %s, emi = %s, maturity = %s, started = %s WHERE sno = %s",
                (data['organisation'], data['value'], data['duration'], data.get('emi'), data['maturity'], data['started'], sno))
    mysql.connection.commit()
    cur.close()
    return jsonify({'message': 'Chit updated successfully'}), 200

# Delete a chit
@bp.route('/api/chits/<int:sno>', methods=['DELETE'])
def delete_chit(sno):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM chits WHERE sno = %s", (sno,))
    mysql.connection.commit()
    cur.close()
    return jsonify({'message': 'Chit deleted successfully'}), 200

