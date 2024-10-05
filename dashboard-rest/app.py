from flask import Flask, request, jsonify
from flask_mysqldb import MySQL
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)

# MySQL configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'teja@4795'
app.config['MYSQL_DB'] = 'teja'

mysql = MySQL(app)

# Fixed Deposits Endpoints

# Get all fixed deposits
@app.route('/api/fixed-deposits', methods=['GET'])
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
@app.route('/api/fixed-deposits', methods=['POST'])
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
@app.route('/api/fixed-deposits/<int:id>', methods=['PUT'])
def update_fixed_deposit(id):
    data = request.json
    cur = mysql.connection.cursor()
    cur.execute("UPDATE fixed_deposits SET bank=%s, invested=%s, interest=%s, maturity_date=%s, created_date=%s WHERE id=%s",
                (data['bank'], data['invested'], data['interest'], data['maturity_date'], data['created_date'], id))
    mysql.connection.commit()
    cur.close()
    return jsonify({'message': 'Fixed deposit updated successfully!'})

# Delete a fixed deposit
@app.route('/api/fixed-deposits/<int:id>', methods=['DELETE'])
def delete_fixed_deposit(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM fixed_deposits WHERE id=%s", (id,))
    mysql.connection.commit()
    cur.close()
    return jsonify({'message': 'Fixed deposit deleted successfully!'})

# Get all savings accounts
@app.route('/api/savings', methods=['GET'])
def get_accounts():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM savings_accounts")
    results = cur.fetchall()
    accounts = [{'id': row[0], 'account_holder': row[1], 'bank_name': row[2], 'savings_account': row[3], 'used_for': row[4]} for row in results]
    cur.close()
    return jsonify(accounts)

# Add a savings account
@app.route('/api/savings', methods=['POST'])
def add_account():
    data = request.json
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO savings_accounts (account_holder, bank_name, savings_account, used_for) VALUES (%s, %s, %s, %s)",
                (data['account_holder'], data['bank_name'], data['savings_account'], data['used_for']))
    mysql.connection.commit()
    cur.close()
    return jsonify({'message': 'Account added successfully!'}), 201

# Update a savings account
@app.route('/api/savings/<int:id>', methods=['PUT'])
def update_account(id):
    data = request.json
    cur = mysql.connection.cursor()
    cur.execute("UPDATE savings_accounts SET account_holder=%s, bank_name=%s, savings_account=%s, used_for=%s WHERE id=%s",
                (data['account_holder'], data['bank_name'], data['savings_account'], data['used_for'], id))
    mysql.connection.commit()
    cur.close()
    return jsonify({'message': 'Account updated successfully!'})

# Delete a savings account
@app.route('/api/savings/<int:id>', methods=['DELETE'])
def delete_account(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM savings_accounts WHERE id=%s", (id,))
    mysql.connection.commit()
    cur.close()
    return jsonify({'message': 'Account deleted successfully!'})

if __name__ == '__main__':
    app.run(debug=True)