from flask import Blueprint, request, jsonify
from flask_mysqldb import MySQL

bp = Blueprint('fixed_deposits', __name__)
mysql = MySQL()
@bp.route('/api/fixed-deposits', methods=['GET'])
def get_fixed_deposits():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM fixed_deposits")
    results = cur.fetchall()
    fixed_deposits = [{'id': row[0], 'bank': row[1], 'invested': row[2], 'interest': row[3], 'maturity_date': row[4].strftime('%Y-%m-%d'),
                       'created_date': row[5].strftime('%Y-%m-%d')}
                      for row in results]
    cur.close()
    return jsonify(fixed_deposits)

# Add a fixed deposit
@bp.route('/api/fixed-deposits', methods=['POST'])
def add_fixed_deposit():
    data = request.json
    print(data)
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO fixed_deposits ( bank, invested, interest, maturity_date, created_date) VALUES ( %s, %s, %s, %s, %s)",
                ( data['bank'], data['invested'], data['interest'], data['maturity_date'], data['created_date']))
    mysql.connection.commit()
    cur.close()
    return jsonify({'message': 'Fixed deposit added successfully!'}), 201

# Update a fixed deposit
@bp.route('/api/fixed-deposits/<int:id>', methods=['PUT'])
def update_fixed_deposit(id):
    data = request.json
    cur = mysql.connection.cursor()
    cur.execute("UPDATE fixed_deposits SET bank=%s, invested=%s, interest=%s, maturity_date=%s, created_date=%s WHERE id=%s",
                (data['bank'], data['invested'], data['interest'], data['maturity_date'], data['created_date'], id))
    mysql.connection.commit()
    cur.close()
    return jsonify({'message': 'Fixed deposit updated successfully!'})

# Delete a fixed deposit
@bp.route('/api/fixed-deposits/<int:id>', methods=['DELETE'])
def delete_fixed_deposit(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM fixed_deposits WHERE id=%s", (id,))
    mysql.connection.commit()
    cur.close()
    return jsonify({'message': 'Fixed deposit deleted successfully!'})

# Get all savings accounts
@bp.route('/api/savings', methods=['GET'])
def get_accounts():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM savings_accounts")
    results = cur.fetchall()
    accounts = [{'id': row[0], 'account_holder': row[1], 'bank_name': row[2], 'savings_account': row[3], 'used_for': row[4]} for row in results]
    cur.close()
    return jsonify(accounts)
