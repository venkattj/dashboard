from flask import Blueprint, request, jsonify
from flask_mysqldb import MySQL

bp = Blueprint('savings', __name__)
mysql = MySQL()

@bp.route('/api/savings', methods=['POST'])
def add_account():
    data = request.json
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO savings_accounts (account_holder, bank_name, savings_account, used_for) VALUES (%s, %s, %s, %s)",
                (data['account_holder'], data['bank_name'], data['savings_account'], data['used_for']))
    mysql.connection.commit()
    cur.close()
    return jsonify({'message': 'Account added successfully!'}), 201

# Update a savings account
@bp.route('/api/savings/<int:id>', methods=['PUT'])
def update_account(id):
    data = request.json
    cur = mysql.connection.cursor()
    cur.execute("UPDATE savings_accounts SET account_holder=%s, bank_name=%s, savings_account=%s, used_for=%s WHERE id=%s",
                (data['account_holder'], data['bank_name'], data['savings_account'], data['used_for'], id))
    mysql.connection.commit()
    cur.close()
    return jsonify({'message': 'Account updated successfully!'})

# Delete a savings account
@bp.route('/api/savings/<int:id>', methods=['DELETE'])
def delete_account(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM savings_accounts WHERE id=%s", (id,))
    mysql.connection.commit()
    cur.close()
    return jsonify({'message': 'Account deleted successfully!'})
