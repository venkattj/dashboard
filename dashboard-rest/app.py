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
# varaible chits

@app.route('/api/variable_chits/<int:chit_id>/emis', methods=['POST'])
def create_emi_for_variable_chit(chit_id):
    data = request.get_json()
    emi_no = data['emi_no']
    amount = data['amount']
    emi_date = data['emi_date']

    try:
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO variable_chits (chit_id, emi_no, amount, emi_date) VALUES (%s, %s, %s, %s)",
                    (chit_id, emi_no, amount, emi_date))
        mysql.connection.commit()
        cur.close()
        return jsonify({'message': 'EMI created successfully!'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/variable_chits/<int:chit_id>/emis', methods=['GET'])
def get_emis_for_variable_chit(chit_id):
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM variable_chits WHERE chit_id = %s", (chit_id,))
        emis = cur.fetchall()
        cur.close()

        return jsonify([
            {
                'id': emi[0],
                'chit_id': emi[1],
                'emi_no': emi[2],
                'amount': emi[3],
                'emi_date': emi[4]
            } for emi in emis
        ]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/variable_chits/<int:chit_id>/emis/<int:emi_id>', methods=['PUT'])
def update_emi_for_variable_chit(chit_id, emi_id):
    data = request.get_json()
    emi_no = data['emi_no']
    amount = data['amount']
    emi_date = data['emi_date']

    try:
        cur = mysql.connection.cursor()
        cur.execute("""
            UPDATE variable_chits 
            SET emi_no = %s, amount = %s, emi_date = %s 
            WHERE id = %s AND chit_id = %s
        """, (emi_no, amount, emi_date, emi_id, chit_id))
        mysql.connection.commit()
        cur.close()
        return jsonify({'message': 'EMI updated successfully!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/variable_chits/<int:chit_id>/emis/<int:emi_id>', methods=['DELETE'])
def delete_emi_for_variable_chit(chit_id, emi_id):
    try:
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM variable_chits WHERE id = %s AND chit_id = %s", (emi_id, chit_id))
        mysql.connection.commit()
        cur.close()
        return jsonify({'message': 'EMI deleted successfully!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/variable_chits', methods=['GET'])
def get_variable_chits():
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM chits WHERE sno IN (SELECT DISTINCT chit_id FROM variable_chits)")
        chits = cur.fetchall()

        variable_chits = []
        for chit in chits:
            cur.execute("SELECT * FROM variable_chits WHERE chit_id = %s", (chit[0],))
            emis = cur.fetchall()
            variable_chits.append({
                'chit_id': chit[0],
                'organisation': chit[1],
                'value': chit[2],
                'duration': chit[3],
                'maturity': chit[5],
                'started': chit[6],
                'emis': [
                    {
                        'emi_no': emi[2],
                        'amount': emi[3],
                        'emi_date': emi[4]
                    } for emi in emis
                ]
            })

        cur.close()
        return jsonify(variable_chits), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# chits
@app.route('/api/chits', methods=['POST'])
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
@app.route('/api/chits', methods=['GET'])
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
@app.route('/api/chits/<int:sno>', methods=['GET'])
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
@app.route('/api/chits/<int:sno>', methods=['PUT'])
def update_chit(sno):
    data = request.get_json()
    cur = mysql.connection.cursor()
    cur.execute("UPDATE chits SET organisation = %s, value = %s, duration = %s, emi = %s, maturity = %s, started = %s WHERE sno = %s",
                (data['organisation'], data['value'], data['duration'], data.get('emi'), data['maturity'], data['started'], sno))
    mysql.connection.commit()
    cur.close()
    return jsonify({'message': 'Chit updated successfully'}), 200

# Delete a chit
@app.route('/api/chits/<int:sno>', methods=['DELETE'])
def delete_chit(sno):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM chits WHERE sno = %s", (sno,))
    mysql.connection.commit()
    cur.close()
    return jsonify({'message': 'Chit deleted successfully'}), 200

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
