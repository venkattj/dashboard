from flask import Blueprint, request, jsonify
from flask_mysqldb import MySQL

bp = Blueprint('earnings', __name__)
mysql = MySQL()

# Add a new earning record
@bp.route('/api/earnings', methods=['POST'])
def add_earning():
    data = request.json
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO earnings (income_type, income_source, amount, earner) VALUES (%s, %s, %s, %s)",
                (data['income_type'], data['income_source'], data['amount'], data['earner']))
    mysql.connection.commit()
    cur.close()
    return jsonify({'message': 'Earning added successfully!'}), 201

# Update an existing earning record
@bp.route('/api/earnings/<int:id>', methods=['PUT'])
def update_earning(id):
    data = request.json
    cur = mysql.connection.cursor()
    cur.execute("UPDATE earnings SET income_type=%s, income_source=%s, amount=%s, earner=%s WHERE id=%s",
                (data['income_type'], data['income_source'], data['amount'], data['earner'], id))
    mysql.connection.commit()
    cur.close()
    return jsonify({'message': 'Earning updated successfully!'})

# Delete an earning record
@bp.route('/api/earnings/<int:id>', methods=['DELETE'])
def delete_earning(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM earnings WHERE id=%s", (id,))
    mysql.connection.commit()
    cur.close()
    return jsonify({'message': 'Earning deleted successfully!'})

# Retrieve all earnings records
@bp.route('/api/earnings', methods=['GET'])
def get_earnings():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, income_type, income_source, amount, earner FROM earnings")
    rows = cur.fetchall()
    cur.close()

    # Structure data into a list of dictionaries
    earnings = []
    for row in rows:
        earnings.append({
            'id': row[0],
            'income_type': row[1],
            'income_source': row[2],
            'amount': float(row[3]),  # Convert to float if using DECIMAL in MySQL
            'earner': row[4]
        })

    return jsonify(earnings)
