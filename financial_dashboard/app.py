from __future__ import annotations

import threading
from datetime import datetime
from pathlib import Path
from typing import Any

import pymysql
from flask import Flask, abort, flash, redirect, render_template, request, url_for

try:
    from .routes.bank_accounts import register_bank_account_routes
    from .routes.chits import register_chits_routes
    from .routes.earnings import register_earnings_routes
    from .routes.fixed_deposits import register_fixed_deposit_routes
    from .routes.loans import register_loans_routes
    from .routes.mutual_funds import register_mutual_funds_routes
    from .routes.overall_assets import register_overall_assets_routes
    from .routes.sneha_payments import register_sneha_payments_routes
    from .routes.spending import register_spending_routes
    from .routes.stocks import register_stocks_routes
    from .routes.utility_bills import register_utility_bills_routes
except ImportError:
    from routes.bank_accounts import register_bank_account_routes
    from routes.chits import register_chits_routes
    from routes.earnings import register_earnings_routes
    from routes.fixed_deposits import register_fixed_deposit_routes
    from routes.loans import register_loans_routes
    from routes.mutual_funds import register_mutual_funds_routes
    from routes.overall_assets import register_overall_assets_routes
    from routes.sneha_payments import register_sneha_payments_routes
    from routes.spending import register_spending_routes
    from routes.stocks import register_stocks_routes
    from routes.utility_bills import register_utility_bills_routes


app = Flask(__name__)
app.secret_key = "financial-dashboard-dev"

WORKBOOK_PATH = Path(r"C:\Users\venka\Desktop\Income\income\Income.xlsx")


ENTITY_CONFIG = {
    "bank_accounts": {
        "title": "Bank Accounts",
        "description": "Cash balances across savings, salary, and operational accounts.",
        "table": "bank_accounts",
        "columns": [
            {"name": "account_holder", "label": "Account Holder", "type": "text"},
            {"name": "bank_name", "label": "Bank Name", "type": "text"},
            {"name": "balance", "label": "Balance", "type": "number", "step": "0.01"},
            {"name": "purpose", "label": "Used For", "type": "text"},
        ],
    },
    "fixed_deposits": {
        "title": "Fixed Deposits",
        "description": "Track maturity dates, invested principal, and current value.",
        "table": "fixed_deposits",
        "columns": [
            {"name": "bank", "label": "Bank", "type": "text"},
            {"name": "invested", "label": "Invested", "type": "number", "step": "0.01"},
            {"name": "interest_rate", "label": "Interest Rate %", "type": "number", "step": "0.01"},
            {"name": "maturity_date", "label": "Maturity Date", "type": "date"},
            {"name": "created_date", "label": "Created Date", "type": "date"},
            {"name": "current_amount", "label": "Current Amount", "type": "number", "step": "0.01"},
            {"name": "days_to_mature", "label": "Days To Mature", "type": "number", "step": "1"},
        ],
    },
    "stocks": {
        "title": "Stocks",
        "description": "Equity holdings with average cost and latest close.",
        "table": "stocks",
        "columns": [
            {"name": "symbol", "label": "Symbol", "type": "text"},
            {"name": "average_price", "label": "Average Price", "type": "number", "step": "0.01"},
            {"name": "current_price", "label": "Current Price", "type": "number", "step": "0.01"},
            {"name": "quantity", "label": "Quantity", "type": "number", "step": "1"},
        ],
    },
    "mutual_funds": {
        "title": "Mutual Funds",
        "description": "SIP and total current value by fund.",
        "table": "mutual_funds",
        "columns": [
            {"name": "fund_name", "label": "Fund Name", "type": "text"},
            {"name": "invested", "label": "Invested", "type": "number", "step": "0.01"},
            {"name": "returns_pct", "label": "Returns %", "type": "number", "step": "0.01"},
            {"name": "sip", "label": "Monthly SIP", "type": "number", "step": "0.01"},
            {"name": "current_value", "label": "Current Value", "type": "number", "step": "0.01"},
        ],
    },
    "utility_bills": {
        "title": "Utility Bills",
        "description": "Recurring household expenses and operating costs.",
        "table": "utility_bills",
        "columns": [
            {"name": "bill_type", "label": "Type", "type": "text"},
            {"name": "amount", "label": "Amount", "type": "number", "step": "0.01"},
        ],
    },
    "loans": {
        "title": "Capital",
        "description": "Capital deployed and capital obligations under one view.",
        "table": "loans",
        "columns": [
            {"name": "borrower", "label": "Given To", "type": "text"},
            {"name": "amount", "label": "Amount", "type": "number", "step": "0.01"},
            {"name": "interest_rate", "label": "Interest Rate %", "type": "number", "step": "0.01"},
        ],
    },
    "earnings": {
        "title": "Earnings",
        "description": "Income across salary, pension, and interest.",
        "table": "earnings",
        "columns": [
            {"name": "income_type", "label": "Type", "type": "text"},
            {"name": "amount", "label": "Amount", "type": "number", "step": "0.01"},
            {"name": "person", "label": "Person", "type": "text"},
            {"name": "source", "label": "From", "type": "text"},
        ],
    },
    "spending": {
        "title": "Spending",
        "description": "Outgoing investments, EMIs, and periodic commitments.",
        "table": "spending",
        "columns": [
            {"name": "spending_type", "label": "Type", "type": "text"},
            {"name": "amount", "label": "Amount", "type": "number", "step": "0.01"},
            {"name": "person", "label": "Person", "type": "text"},
            {"name": "recipient", "label": "To", "type": "text"},
        ],
    },
    "standard_chits": {
        "title": "Standard Chits",
        "description": "Traditional chits with tenure, installments, and maturity.",
        "table": "standard_chits",
        "columns": [
            {"name": "organization", "label": "Organization", "type": "text"},
            {"name": "value", "label": "Value", "type": "number", "step": "0.01"},
            {"name": "duration_months", "label": "Duration", "type": "number", "step": "1"},
            {"name": "paid_months", "label": "Paid Months", "type": "number", "step": "1"},
            {"name": "emi", "label": "EMI", "type": "number", "step": "0.01"},
            {"name": "maturity_date", "label": "Maturity Date", "type": "date"},
            {"name": "started_date", "label": "Started Date", "type": "date"},
            {"name": "current_value", "label": "Current Value", "type": "number", "step": "0.01"},
            {"name": "note", "label": "Note", "type": "text"},
        ],
    },
    "variable_chits": {
        "title": "Variable Chits",
        "description": "Variable contribution chits with payout and net value tracking.",
        "table": "variable_chits",
        "columns": [
            {"name": "name", "label": "Name", "type": "text"},
            {"name": "value", "label": "Value", "type": "number", "step": "0.01"},
            {"name": "months", "label": "Months", "type": "number", "step": "1"},
            {"name": "maturity_date", "label": "Maturity Date", "type": "date"},
            {"name": "total_paid", "label": "Total Paid", "type": "number", "step": "0.01"},
            {"name": "start_date", "label": "Start Date", "type": "date"},
            {"name": "net_value", "label": "Net Value", "type": "number", "step": "0.01"},
            {"name": "emi_paid", "label": "EMIs Paid", "type": "number", "step": "1"},
        ],
    },
    "variable_chit_payments": {
        "title": "Variable Chit Payments",
        "description": "Installment history for the variable chit.",
        "table": "variable_chit_payments",
        "columns": [
            {"name": "emi_no", "label": "EMI No", "type": "number", "step": "1"},
            {"name": "amount", "label": "Amount", "type": "number", "step": "0.01"},
            {"name": "payment_date", "label": "Date", "type": "date"},
            {"name": "actual_paid", "label": "Actual Paid", "type": "number", "step": "0.01"},
            {"name": "start_date", "label": "Chit Start", "type": "date"},
        ],
    },
    "sneha_payments": {
        "title": "Sneha Payments",
        "description": "Payment schedule and outstanding principal for Sneha.",
        "table": "sneha_payments",
        "columns": [
            {"name": "payment_date", "label": "Date", "type": "date"},
            {"name": "amount", "label": "Amount", "type": "number", "step": "0.01"},
            {"name": "principal_balance", "label": "Principal Balance", "type": "number", "step": "0.01"},
        ],
    },
    "overall_assets": {
        "title": "Overall Assets",
        "description": "Imported long-term holdings and balance sheet items.",
        "table": "overall_assets",
        "columns": [
            {"name": "label", "label": "Label", "type": "text"},
            {"name": "amount", "label": "Amount", "type": "number", "step": "0.01"},
            {"name": "note", "label": "Note", "type": "text"},
        ],
    },
}


DB_LOCK = threading.Lock()


class Config:
    MYSQL_HOST = "localhost"
    MYSQL_USER = "root"
    MYSQL_PASSWORD = "teja@4795"
    MYSQL_DB = "teja"


def as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def as_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default




def reset_database() -> None:
    with DB_LOCK:
        try:
            from .db.mysql_seed import create_database, create_tables, truncate_tables, seed_tables
        except ImportError:
            from db.mysql_seed import create_database, create_tables, truncate_tables, seed_tables

        create_database()
        create_tables()
        truncate_tables()
        seed_tables(WORKBOOK_PATH)


def ensure_database_ready() -> None:
    with DB_LOCK:
        try:
            from .db.mysql_seed import create_database, create_tables, truncate_tables, seed_tables
        except ImportError:
            from db.mysql_seed import create_database, create_tables, truncate_tables, seed_tables

        create_database()
        create_tables()

        with pymysql.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB,
            charset="utf8mb4",
            autocommit=True,
            cursorclass=pymysql.cursors.DictCursor,
        ) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) AS count FROM bank_accounts")
                row = cur.fetchone()
                if row and row["count"] == 0 and WORKBOOK_PATH.exists():
                    truncate_tables()
                    seed_tables(WORKBOOK_PATH)


def get_connection():
    return pymysql.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB,
        charset="utf8mb4",
        autocommit=True,
        cursorclass=pymysql.cursors.DictCursor,
    )


def adapt_query(query: str) -> str:
    return query.replace("?", "%s")


def fetch_all(query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(adapt_query(query), params)
            return cur.fetchall()


def fetch_one(query: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(adapt_query(query), params)
            return cur.fetchone()


def execute(query: str, params: tuple[Any, ...] = ()) -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(adapt_query(query), params)


def format_currency(value: float | None) -> str:
    amount = value or 0
    return f"Rs. {amount:,.2f}"


def format_number(value: float | None) -> str:
    amount = value or 0
    return f"{amount:,.2f}"


def format_cell(value: Any, column: dict[str, Any]) -> str:
    if value is None or value == "":
        return "-"
    if column["type"] != "number":
        return str(value)

    name = column["name"]
    if "rate" in name or "pct" in name:
        return f"{format_number(as_float(value))}%"
    if name in {"quantity", "days_to_mature", "emi_no", "duration_months", "paid_months", "months", "emi_paid"}:
        return format_number(as_float(value))
    return format_currency(as_float(value))


def today_string() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def build_dashboard_metrics() -> dict[str, Any]:
    totals = {
        "bank": fetch_one("SELECT COALESCE(SUM(balance), 0) AS total FROM bank_accounts")["total"],
        "fd": fetch_one("SELECT COALESCE(SUM(current_amount), 0) AS total FROM fixed_deposits")["total"],
        "stocks": fetch_one("SELECT COALESCE(SUM(current_price * quantity), 0) AS total FROM stocks")["total"],
        "mutual_funds": fetch_one("SELECT COALESCE(SUM(current_value), 0) AS total FROM mutual_funds")["total"],
        "loans_receivable": fetch_one("SELECT COALESCE(SUM(amount), 0) AS total FROM loans WHERE amount > 0")["total"],
        "loan_obligations": fetch_one("SELECT ABS(COALESCE(SUM(amount), 0)) AS total FROM loans WHERE amount < 0")[
            "total"
        ],
        "chits": fetch_one(
            "SELECT COALESCE((SELECT SUM(current_value) FROM standard_chits), 0) + "
            "COALESCE((SELECT SUM(net_value) FROM variable_chits), 0) AS total"
        )["total"],
        "other": fetch_one(
            "SELECT COALESCE(SUM(amount), 0) AS total FROM overall_assets "
            "WHERE label IN ('Gratuity', 'nps', 'PF', 'JPMC Stocks')"
        )["total"],
    }
    asset_total = (
        totals["bank"]
        + totals["fd"]
        + totals["stocks"]
        + totals["mutual_funds"]
        + totals["loans_receivable"]
        + totals["chits"]
        + totals["other"]
    )
    net_worth = asset_total - totals["loan_obligations"]

    monthly_income = fetch_one("SELECT COALESCE(SUM(amount), 0) AS total FROM earnings")["total"]
    monthly_spend = fetch_one(
        "SELECT COALESCE((SELECT SUM(amount) FROM spending), 0) + "
        "COALESCE((SELECT SUM(amount) FROM utility_bills), 0) AS total"
    )["total"]

    upcoming_fds = fetch_all(
        "SELECT bank, maturity_date, current_amount, days_to_mature "
        "FROM fixed_deposits WHERE days_to_mature BETWEEN 0 AND 120 "
        "ORDER BY days_to_mature ASC LIMIT 5"
    )
    highest_balances = fetch_all(
        "SELECT account_holder, bank_name, balance FROM bank_accounts ORDER BY balance DESC LIMIT 5"
    )
    biggest_expenses = fetch_all(
        "SELECT spending_type, person, recipient, amount FROM spending ORDER BY amount DESC LIMIT 5"
    )
    asset_mix = [
        {"label": "Bank", "amount": totals["bank"]},
        {"label": "Fixed Deposits", "amount": totals["fd"]},
        {"label": "Stocks", "amount": totals["stocks"]},
        {"label": "Mutual Funds", "amount": totals["mutual_funds"]},
        {"label": "Loans Given", "amount": totals["loans_receivable"]},
        {"label": "Chits", "amount": totals["chits"]},
        {"label": "Other Assets", "amount": totals["other"]},
    ]
    largest_asset = max((item["amount"] for item in asset_mix), default=1) or 1

    stock_positions = []
    for row in fetch_all("SELECT symbol, average_price, current_price, quantity FROM stocks ORDER BY current_price * quantity DESC"):
        market_value = row["current_price"] * row["quantity"]
        cost_value = row["average_price"] * row["quantity"]
        stock_positions.append(
            {
                "symbol": row["symbol"],
                "market_value": market_value,
                "pnl": market_value - cost_value,
            }
        )
    top_stock_moves = sorted(stock_positions, key=lambda item: item["pnl"], reverse=True)[:5]
    draggers = sorted(stock_positions, key=lambda item: item["pnl"])[:5]

    return {
        "generated_on": today_string(),
        "asset_total": asset_total,
        "net_worth": net_worth,
        "monthly_income": monthly_income,
        "monthly_spend": monthly_spend,
        "monthly_surplus": monthly_income - monthly_spend,
        "loan_obligations": totals["loan_obligations"],
        "asset_mix": asset_mix,
        "largest_asset": largest_asset,
        "upcoming_fds": upcoming_fds,
        "highest_balances": highest_balances,
        "biggest_expenses": biggest_expenses,
        "top_stock_moves": top_stock_moves,
        "draggers": draggers,
    }


def serialize_form(entity_key: str, form_data: Any) -> dict[str, Any]:
    entity = ENTITY_CONFIG[entity_key]
    values: dict[str, Any] = {}
    for column in entity["columns"]:
        raw = form_data.get(column["name"], "").strip()
        if column["type"] == "number":
            values[column["name"]] = as_float(raw)
        else:
            values[column["name"]] = raw
    return values


def build_generic_entity_context(entity_key: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    entity = ENTITY_CONFIG[entity_key]
    numeric_columns = [column for column in entity["columns"] if column["type"] == "number"]
    text_columns = [column for column in entity["columns"] if column["type"] == "text"]

    primary_numeric = numeric_columns[0] if numeric_columns else None
    total_value = sum(as_float(row[primary_numeric["name"]]) for row in rows) if primary_numeric else None
    average_value = (total_value / len(rows)) if primary_numeric and rows else None
    top_row = max(rows, key=lambda row: as_float(row[primary_numeric["name"]])) if primary_numeric and rows else None

    filter_options: dict[str, list[str]] = {}
    for column in text_columns:
        values = sorted(
            {
                (row[column["name"]] or "").strip() if isinstance(row[column["name"]], str) else str(row[column["name"]] or "")
                for row in rows
                if row[column["name"]] is not None and str(row[column["name"]]).strip()
            }
        )
        filter_options[column["name"]] = values

    return {
        "summary": {
            "record_count": len(rows),
            "primary_numeric": primary_numeric,
            "total_value": total_value,
            "average_value": average_value,
            "top_row": top_row,
        },
        "filter_options": filter_options,
    }


def record_label(entity_key: str) -> str:
    return ENTITY_CONFIG[entity_key]["title"]


register_bank_account_routes(
    app=app,
    entity_config=ENTITY_CONFIG,
    fetch_all=fetch_all,
    execute=execute,
    as_float=as_float,
)
register_fixed_deposit_routes(
    app=app,
    entity_config=ENTITY_CONFIG,
    fetch_all=fetch_all,
    execute=execute,
    as_float=as_float,
    as_int=as_int,
)
register_stocks_routes(
    app=app,
    entity_config=ENTITY_CONFIG,
    fetch_all=fetch_all,
    as_float=as_float,
)
register_loans_routes(
    app=app,
    entity_config=ENTITY_CONFIG,
    fetch_all=fetch_all,
    as_float=as_float,
)
register_chits_routes(
    app=app,
    entity_config=ENTITY_CONFIG,
    fetch_all=fetch_all,
    as_float=as_float,
    as_int=as_int,
)
register_utility_bills_routes(
    app=app,
    entity_config=ENTITY_CONFIG,
    fetch_all=fetch_all,
    as_float=as_float,
)
register_spending_routes(
    app=app,
    entity_config=ENTITY_CONFIG,
    fetch_all=fetch_all,
    as_float=as_float,
)
register_earnings_routes(
    app=app,
    entity_config=ENTITY_CONFIG,
    fetch_all=fetch_all,
    as_float=as_float,
)
register_sneha_payments_routes(
    app=app,
    entity_config=ENTITY_CONFIG,
    fetch_all=fetch_all,
    as_float=as_float,
)
register_overall_assets_routes(
    app=app,
    entity_config=ENTITY_CONFIG,
    fetch_all=fetch_all,
    as_float=as_float,
)
register_mutual_funds_routes(
    app=app,
    entity_config=ENTITY_CONFIG,
    fetch_all=fetch_all,
    as_float=as_float,
)


@app.context_processor
def inject_helpers() -> dict[str, Any]:
    return {
        "entities": ENTITY_CONFIG,
        "format_currency": format_currency,
        "format_number": format_number,
        "format_cell": format_cell,
    }


@app.get("/")
def dashboard() -> str:
    return render_template("dashboard.html", metrics=build_dashboard_metrics())


@app.post("/reload")
def reload_data():
    if not WORKBOOK_PATH.exists():
        flash(f"Workbook not found at {WORKBOOK_PATH}", "error")
        return redirect(url_for("dashboard"))
    reset_database()
    flash("Dashboard data was reloaded from the Excel workbook.", "success")
    return redirect(url_for("dashboard"))


@app.get("/entity/<entity_key>")
def entity_list(entity_key: str) -> str:
    entity = ENTITY_CONFIG.get(entity_key)
    if entity is None:
        abort(404)
    search = request.args.get("q", "").strip()
    columns = entity["columns"]
    query = f"SELECT * FROM {entity['table']}"
    params: tuple[Any, ...] = ()
    if search:
        filters = []
        for column in columns:
            if column["type"] == "text":
                filters.append(f"{column['name']} LIKE ?")
                params += (f"%{search}%",)
        if filters:
            query += " WHERE " + " OR ".join(filters)
    query += " ORDER BY id DESC"
    rows = fetch_all(query, params)
    context = build_generic_entity_context(entity_key, rows)
    return render_template(
        "entity_list.html",
        entity_key=entity_key,
        entity=entity,
        rows=rows,
        search=search,
        **context,
    )

@app.post("/entity/<entity_key>/<int:row_id>/inline-update")
def entity_inline_update(entity_key: str, row_id: int):
    entity = ENTITY_CONFIG.get(entity_key)
    if entity is None:
        abort(404)

    values = serialize_form(entity_key, request.form)
    assignments = ", ".join(f"{name} = ?" for name in values)
    execute(
        f"UPDATE {entity['table']} SET {assignments} WHERE id = ?",
        tuple(values.values()) + (row_id,),
    )
    flash(f"{record_label(entity_key)} row updated.", "success")
    return redirect(url_for("entity_list", entity_key=entity_key))


@app.route("/entity/<entity_key>/new", methods=["GET", "POST"])
def entity_create(entity_key: str) -> str:
    entity = ENTITY_CONFIG.get(entity_key)
    if entity is None:
        abort(404)
    if request.method == "POST":
        values = serialize_form(entity_key, request.form)
        columns = list(values.keys())
        execute(
            f"INSERT INTO {entity['table']} ({', '.join(columns)}) VALUES ({', '.join('?' for _ in columns)})",
            tuple(values[column] for column in columns),
        )
        flash(f"{record_label(entity_key)} record added successfully.", "success")
        return redirect(url_for("entity_list", entity_key=entity_key))
    return render_template("entity_form.html", entity_key=entity_key, entity=entity, row={})


@app.route("/entity/<entity_key>/<int:row_id>/edit", methods=["GET", "POST"])
def entity_edit(entity_key: str, row_id: int) -> str:
    entity = ENTITY_CONFIG.get(entity_key)
    if entity is None:
        abort(404)
    row = fetch_one(f"SELECT * FROM {entity['table']} WHERE id = ?", (row_id,))
    if row is None:
        abort(404)
    if request.method == "POST":
        values = serialize_form(entity_key, request.form)
        assignments = ", ".join(f"{name} = ?" for name in values)
        execute(
            f"UPDATE {entity['table']} SET {assignments} WHERE id = ?",
            tuple(values.values()) + (row_id,),
        )
        flash(f"{record_label(entity_key)} record updated successfully.", "success")
        return redirect(url_for("entity_list", entity_key=entity_key))
    return render_template("entity_form.html", entity_key=entity_key, entity=entity, row=row)


@app.post("/entity/<entity_key>/<int:row_id>/delete")
def entity_delete(entity_key: str, row_id: int):
    entity = ENTITY_CONFIG.get(entity_key)
    if entity is None:
        abort(404)
    execute(f"DELETE FROM {entity['table']} WHERE id = ?", (row_id,))
    flash(f"{record_label(entity_key)} record deleted.", "success")
    return redirect(url_for("entity_list", entity_key=entity_key))


ensure_database_ready()


if __name__ == "__main__":
    app.run(debug=True, use_reloader=True)
