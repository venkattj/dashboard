from flask import Flask
from flask_mysqldb import MySQL
from flask_cors import CORS
from config import Config
from routes import variable_chits, chits, fixed_deposits, savings, home_loans,db_routes, ui_routes, investments , earnings,spendings, loans_given  # Import the new investments blueprint

app = Flask(__name__, static_folder='../dashboard-app/build')
app.config.from_object(Config)
CORS(app)

mysql = MySQL(app)

# Register Blueprints for different routes
app.register_blueprint(variable_chits.bp)
app.register_blueprint(chits.bp)
app.register_blueprint(fixed_deposits.bp)
app.register_blueprint(savings.bp)
app.register_blueprint(home_loans.bp)
app.register_blueprint(db_routes.bp)
app.register_blueprint(ui_routes.bp)
app.register_blueprint(investments.bp)
app.register_blueprint(earnings.bp)
app.register_blueprint(spendings.bp)
app.register_blueprint(loans_given.bp)
if __name__ == '__main__':
    app.run(debug=True)
