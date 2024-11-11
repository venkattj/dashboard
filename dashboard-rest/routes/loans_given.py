from flask import Blueprint, request, jsonify
from flask_mysqldb import MySQL

bp = Blueprint('loans_given', __name__)
mysql = MySQL()

# Add a new loan given record
@bp.route('/api/loans_given', methods=['POST'])
def add_loan():
    data = request.json
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO loans_given (receiver, amount, interest_rate, source) VALUES (%s, %s, %s, %s)",
                (data['receiver'], data['amount'], data['interest_rate'], data['source']))
    mysql.connection.commit()
    cur.close()
    return jsonify({'message': 'Loan added successfully!'}), 201

# Update an existing loan given record
@bp.route('/api/loans_given/<int:id>', methods=['PUT'])
def update_loan(id):
    data = request.json
    cur = mysql.connection.cursor()
    cur.execute("UPDATE loans_given SET receiver=%s, amount=%s, interest_rate=%s, source=%s WHERE id=%s",
                (data['receiver'], data['amount'], data['interest_rate'], data['source'], id))
    mysql.connection.commit()
    cur.close()
    return jsonify({'message': 'Loan updated successfully!'})

# Delete a loan given record
@bp.route('/api/loans_given/<int:id>', methods=['DELETE'])
def delete_loan(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM loans_given WHERE id=%s", (id,))
    mysql.connection.commit()
    cur.close()
    return jsonify({'message': 'Loan deleted successfully!'})

# Retrieve all loans given records
@bp.route('/api/loans_given', methods=['GET'])
def get_loans():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, receiver, amount, interest_rate, source FROM loans_given")
    rows = cur.fetchall()
    cur.close()

    # Structure data into a list of dictionaries
    loans = []
    print(rows)
    for row in rows:
        loans.append({
            'id': row[0],
            'receiver': row[1],
            'amount': float(row[2]),  # Convert to float if using DECIMAL in MySQL
            'interest_rate': float(row[3]),
            'source': row[4]
        })

    return jsonify(loans)
