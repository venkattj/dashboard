from flask import Blueprint, request, jsonify
from flask_mysqldb import MySQL

bp = Blueprint('spendings', __name__)
mysql = MySQL()

# Add a spending
@bp.route('/api/spendings', methods=['POST'])
def add_spending():
    data = request.json
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO spendings (sno, expense_type, amount, spender, merchant) VALUES (%s, %s, %s, %s, %s)",
                (data['sno'], data['expense_type'], data['amount'], data['spender'], data['merchant']))
    mysql.connection.commit()
    cur.close()
    return jsonify({'message': 'Spending added successfully!'}), 201

# Update a spending
@bp.route('/api/spendings/<int:id>', methods=['PUT'])
def update_spending(id):
    data = request.json
    cur = mysql.connection.cursor()
    cur.execute("UPDATE spendings SET sno=%s, expense_type=%s, amount=%s, spender=%s, merchant=%s WHERE id=%s",
                (data['sno'], data['expense_type'], data['amount'], data['spender'], data['merchant'], id))
    mysql.connection.commit()
    cur.close()
    return jsonify({'message': 'Spending updated successfully!'})

# Delete a spending
@bp.route('/api/spendings/<int:id>', methods=['DELETE'])
def delete_spending(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM spendings WHERE id=%s", (id,))
    mysql.connection.commit()
    cur.close()
    return jsonify({'message': 'Spending deleted successfully!'})

# Get all spendings
@bp.route('/api/spendings', methods=['GET'])
def get_spendings():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM spendings")
    rows = cur.fetchall()
    cur.close()
    spendings = [{'id': row[0], 'sno': row[1], 'expense_type': row[2], 'amount': row[3],
                  'spender': row[4], 'merchant': row[5]} for row in rows]
    return jsonify(spendings)
