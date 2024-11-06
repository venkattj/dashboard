from flask import Blueprint, request, jsonify
from flask_mysqldb import MySQL

bp = Blueprint('investments', __name__)
mysql = MySQL()

# Add investment
@bp.route('/api/investments', methods=['POST'])
def add_investment():
    data = request.json
    # Validate the request data
    required_fields = ['sno', 'investment_type', 'invested_amount', 'current_amount', 'sip_amount', 'sip_date']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400

    cur = mysql.connection.cursor()
    try:
        cur.execute(
            "INSERT INTO investments (sno, investment_type, invested_amount, current_amount, sip_amount, sip_date) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (data['sno'], data['investment_type'], data['invested_amount'], data['current_amount'], data['sip_amount'], data['sip_date'])
        )
        mysql.connection.commit()
        cur.close()
        return jsonify({'message': 'Investment added successfully!'}), 201
    except Exception as e:
        cur.close()
        return jsonify({'error': str(e)}), 500


# Update investment
@bp.route('/api/investments/<int:id>', methods=['PUT'])
def update_investment(id):
    data = request.json
    # Validate the request data
    required_fields = ['sno', 'investment_type', 'invested_amount', 'current_amount', 'sip_amount', 'sip_date']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400

    cur = mysql.connection.cursor()
    try:
        cur.execute(
            "UPDATE investments SET sno=%s, investment_type=%s, invested_amount=%s, current_amount=%s, sip_amount=%s, sip_date=%s WHERE id=%s",
            (data['sno'], data['investment_type'], data['invested_amount'], data['current_amount'], data['sip_amount'], data['sip_date'], id)
        )
        mysql.connection.commit()
        cur.close()
        return jsonify({'message': 'Investment updated successfully!'})
    except Exception as e:
        cur.close()
        return jsonify({'error': str(e)}), 500


# Delete investment
@bp.route('/api/investments/<int:id>', methods=['DELETE'])
def delete_investment(id):
    cur = mysql.connection.cursor()
    try:
        cur.execute("DELETE FROM investments WHERE id=%s", (id,))
        mysql.connection.commit()
        cur.close()
        return jsonify({'message': 'Investment deleted successfully!'})
    except Exception as e:
        cur.close()
        return jsonify({'error': str(e)}), 500

# Fetch all investments
@bp.route('/api/investments', methods=['GET'])
def get_investments():
    cur = mysql.connection.cursor()
    try:
        cur.execute("SELECT * FROM investments")
        investments = cur.fetchall()
        cur.close()

        # Convert the result to a list of dictionaries
        investments_list = []
        for investment in investments:
            investments_list.append({
                'id': investment[0],
                'sno': investment[1],
                'investment_type': investment[2],
                'invested_amount': investment[3],
                'current_amount': investment[4],
                'sip_amount': investment[5],
                'sip_date': investment[6].strftime('%Y-%m-%d')
            })

        return jsonify(investments_list), 200

    except Exception as e:
        cur.close()
        return jsonify({'error': str(e)}), 500
