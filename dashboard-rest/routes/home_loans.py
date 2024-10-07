from flask import Blueprint, request, jsonify
from flask_mysqldb import MySQL

bp = Blueprint('home_loans', __name__)
mysql = MySQL()

@bp.route('/homeloans', methods=['GET'])
def get_homeloans():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM home_loan")
    result = cur.fetchall()
    cur.close()

    loans = []
    for row in result:
        loans.append({
            'loan_number': row[0],
            'area_office': row[1],
            'date_of_sanction': row[2].strftime('%Y-%m-%d'),
            'sanction_amount': row[3],
            'first_disbursement': row[4].strftime('%Y-%m-%d'),
            'disbursement_amount': row[5],
            'roi': row[6],
            'emi': row[7],
            'fup': row[8].strftime('%Y-%m-%d'),
            'unpaid_installments': row[9],
            'principal_outstanding': row[10],
            'loan_end_date': row[11].strftime('%Y-%m-%d'),
            'last_emi_paid': row[12],
            'principal_repaid_current_fy': row[13],
            'interest_paid_current_fy': row[14],
            'premium_paid_current_fy': row[15]
        })

    return jsonify(loans)

# Get a single home loan by loan_number
@bp.route('/homeloans/<loan_number>', methods=['GET'])
def get_homeloan(loan_number):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM home_loan WHERE loan_number = %s", [loan_number])
    result = cur.fetchone()
    cur.close()

    if result:
        loan = {
            'loan_number': result[0],
            'area_office': result[1],
            'date_of_sanction': result[2].strftime('%Y-%m-%d'),
            'sanction_amount': result[3],
            'first_disbursement': result[4].strftime('%Y-%m-%d'),
            'disbursement_amount': result[5],
            'roi': result[6],
            'emi': result[7],
            'fup': result[8].strftime('%Y-%m-%d'),
            'unpaid_installments': result[9],
            'principal_outstanding': result[10],
            'loan_end_date': result[11].strftime('%Y-%m-%d'),
            'last_emi_paid': result[12],
            'principal_repaid_current_fy': result[13],
            'interest_paid_current_fy': result[14],
            'premium_paid_current_fy': result[15]
        }
        return jsonify(loan)
    else:
        return jsonify({'message': 'Loan not found'}), 404

# Create a new home loan record
@bp.route('/homeloans', methods=['POST'])
def create_homeloan():
    data = request.json
    cur = mysql.connection.cursor()
    cur.execute(
        "INSERT INTO home_loan (loan_number, area_office, date_of_sanction, sanction_amount, first_disbursement, disbursement_amount, roi, emi, fup, unpaid_installments, principal_outstanding, loan_end_date, last_emi_paid, principal_repaid_current_fy, interest_paid_current_fy, premium_paid_current_fy) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
        (data['loan_number'], data['area_office'], data['date_of_sanction'], data['sanction_amount'], data['first_disbursement'],
         data['disbursement_amount'], data['roi'], data['emi'], data['fup'], data['unpaid_installments'],
         data['principal_outstanding'], data['loan_end_date'], data['last_emi_paid'], data['principal_repaid_current_fy'],
         data['interest_paid_current_fy'], data['premium_paid_current_fy'])
    )
    mysql.connection.commit()
    cur.close()
    return jsonify({'message': 'Loan record created successfully'})

# Update an existing home loan record
@bp.route('/homeloans/<loan_number>', methods=['PUT'])
def update_homeloan(loan_number):
    data = request.json
    cur = mysql.connection.cursor()
    cur.execute(
        "UPDATE home_loan SET area_office=%s, date_of_sanction=%s, sanction_amount=%s, first_disbursement=%s, disbursement_amount=%s, roi=%s, emi=%s, fup=%s, unpaid_installments=%s, principal_outstanding=%s, loan_end_date=%s, last_emi_paid=%s, principal_repaid_current_fy=%s, interest_paid_current_fy=%s, premium_paid_current_fy=%s WHERE loan_number=%s",
        (data['area_office'], data['date_of_sanction'], data['sanction_amount'], data['first_disbursement'],
         data['disbursement_amount'], data['roi'], data['emi'], data['fup'], data['unpaid_installments'],
         data['principal_outstanding'], data['loan_end_date'], data['last_emi_paid'], data['principal_repaid_current_fy'],
         data['interest_paid_current_fy'], data['premium_paid_current_fy'], loan_number)
    )
    mysql.connection.commit()
    cur.close()
    return jsonify({'message': 'Loan record updated successfully'})

# Delete a home loan record
@bp.route('/homeloans/<loan_number>', methods=['DELETE'])
def delete_homeloan(loan_number):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM home_loan WHERE loan_number = %s", [loan_number])
    mysql.connection.commit()
    cur.close()
    return jsonify({'message': 'Loan record deleted successfully'})


