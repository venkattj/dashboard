from flask import Blueprint, request, jsonify
from flask_mysqldb import MySQL

bp = Blueprint('variable_chits', __name__)
mysql = MySQL()

@bp.route('/api/variable_chits/<int:chit_id>/emis', methods=['POST'])
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

@bp.route('/api/variable_chits/<int:chit_id>/emis', methods=['GET'])
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

@bp.route('/api/variable_chits/<int:chit_id>/emis/<int:emi_id>', methods=['PUT'])
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

@bp.route('/api/variable_chits/<int:chit_id>/emis/<int:emi_id>', methods=['DELETE'])
def delete_emi_for_variable_chit(chit_id, emi_id):
    try:
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM variable_chits WHERE id = %s AND chit_id = %s", (emi_id, chit_id))
        mysql.connection.commit()
        cur.close()
        return jsonify({'message': 'EMI deleted successfully!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/api/variable_chits', methods=['GET'])
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
                'maturity': chit[5].strftime('%Y-%m-%d'),
                'started': chit[6].strftime('%Y-%m-%d'),
                'emis': [
                    {
                        'id': emi[0],
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
