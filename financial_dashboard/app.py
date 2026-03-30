from __future__ import annotations

import hashlib
import json
import threading
import zipfile
from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit
from urllib.parse import urlencode
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from xml.sax.saxutils import escape

import pymysql
from flask import Flask, abort, flash, redirect, render_template, request, send_file, session, url_for
from itsdangerous import URLSafeSerializer
from werkzeug.security import check_password_hash, generate_password_hash

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
LOGIN_ENDPOINT = "login"
SIGNUP_ENDPOINT = "signup"
ZERODHA_CALLBACK_ENDPOINT = "zerodha_callback"
AUTH_EXEMPT_ENDPOINTS = {LOGIN_ENDPOINT, SIGNUP_ENDPOINT, ZERODHA_CALLBACK_ENDPOINT, "static"}


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
            {"name": "account_id", "label": "Account ID", "type": "number", "step": "1"},
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
            {"name": "exchange", "label": "Exchange", "type": "text"},
            {"name": "isin", "label": "ISIN", "type": "text"},
            {"name": "average_price", "label": "Average Price", "type": "number", "step": "0.01"},
            {"name": "current_price", "label": "Current Price", "type": "number", "step": "0.01"},
            {"name": "quantity", "label": "Quantity", "type": "number", "step": "1"},
            {"name": "source", "label": "Source", "type": "text"},
            {"name": "last_synced_price_at", "label": "Price Synced At", "type": "text"},
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


def sync_bank_account_reference_data() -> None:
    return None


def fetch_bank_account_rows(order_by: str = "ba.balance DESC, ba.id DESC") -> list[dict[str, Any]]:
    return fetch_all(
        f"""
        SELECT
            ba.id,
            ba.user_id,
            ba.bank_id,
            u.full_name AS account_holder,
            b.name AS bank_name,
            ba.balance,
            ba.purpose
        FROM bank_accounts ba
        LEFT JOIN users u ON u.id = ba.user_id
        LEFT JOIN banks b ON b.id = ba.bank_id
        ORDER BY {order_by}
        """
    )


def ensure_bank_account_entities(account_holder: str, bank_name: str) -> tuple[int, int]:
    holder = normalize_text(account_holder)
    bank = normalize_text(bank_name)
    if not holder or not bank:
        raise ValueError("Account holder and bank name are required.")

    user = fetch_one("SELECT id FROM users WHERE full_name = ?", (holder,))
    if user is None:
        execute("INSERT INTO users (full_name) VALUES (?)", (holder,))
        user = fetch_one("SELECT id FROM users WHERE full_name = ?", (holder,))

    bank_row = fetch_one("SELECT id FROM banks WHERE name = ?", (bank,))
    if bank_row is None:
        execute("INSERT INTO banks (name) VALUES (?)", (bank,))
        bank_row = fetch_one("SELECT id FROM banks WHERE name = ?", (bank,))

    if user is None or bank_row is None:
        raise ValueError("Could not resolve bank account references.")
    return user["id"], bank_row["id"]


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


def is_safe_redirect_target(target: str | None) -> bool:
    if not target:
        return False
    parts = urlsplit(target)
    return not parts.scheme and not parts.netloc and target.startswith("/")


def get_post_login_redirect() -> str:
    target = request.args.get("next") or request.form.get("next")
    if is_safe_redirect_target(target):
        return target
    return url_for("dashboard")


def is_authenticated() -> bool:
    return bool(session.get("authenticated") and session.get("user_id"))


def normalize_text(value: Any) -> str:
    return str(value or "").strip()


def current_timestamp_string() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def zerodha_state_serializer() -> URLSafeSerializer:
    return URLSafeSerializer(app.secret_key, salt="zerodha-connect")


def get_auth_user_by_username(username: str) -> dict[str, Any] | None:
    return fetch_one(
        """
        SELECT id, full_name, username, email, password_hash
        FROM users
        WHERE username = ? AND password_hash IS NOT NULL
        """,
        (username,),
    )


def username_exists(username: str) -> bool:
    row = fetch_one("SELECT id FROM users WHERE username = ?", (username,))
    return row is not None


def email_exists(email: str) -> bool:
    row = fetch_one("SELECT id FROM users WHERE email = ?", (email,))
    return row is not None


def full_name_exists(full_name: str) -> bool:
    row = fetch_one("SELECT id FROM users WHERE full_name = ?", (full_name,))
    return row is not None


def get_user_by_full_name(full_name: str) -> dict[str, Any] | None:
    return fetch_one(
        """
        SELECT id, full_name, username, email, password_hash
        FROM users
        WHERE full_name = ?
        """,
        (full_name,),
    )


def get_current_user() -> dict[str, Any] | None:
    user_id = session.get("user_id")
    if not user_id:
        return None
    return fetch_one("SELECT * FROM users WHERE id = ?", (user_id,))


def establish_user_session(user: dict[str, Any]) -> None:
    session.clear()
    session["authenticated"] = True
    session["user_id"] = user["id"]
    session["username"] = user["username"]
    session["full_name"] = user["full_name"]


def create_or_upgrade_auth_user(full_name: str, username: str, email: str, password: str) -> None:
    existing = get_user_by_full_name(full_name)
    password_hash = generate_password_hash(password)
    if existing is None:
        execute(
            """
            INSERT INTO users (full_name, username, email, password_hash)
            VALUES (?, ?, ?, ?)
            """,
            (full_name, username, email, password_hash),
        )
        return

    execute(
        """
        UPDATE users
        SET username = ?, email = ?, password_hash = ?
        WHERE id = ?
        """,
        (username, email, password_hash, existing["id"]),
    )


def verify_login(username: str, password: str) -> dict[str, Any] | None:
    user = get_auth_user_by_username(username)
    if user and check_password_hash(user["password_hash"], password):
        return user
    return None


def save_zerodha_credentials(user_id: int, api_key: str, api_secret: str) -> None:
    execute(
        """
        UPDATE users
        SET zerodha_api_key = ?, zerodha_api_secret = ?
        WHERE id = ?
        """,
        (api_key, api_secret, user_id),
    )


def clear_zerodha_connection(user_id: int) -> None:
    execute(
        """
        UPDATE users
        SET
            zerodha_access_token = NULL,
            zerodha_public_token = NULL,
            zerodha_user_id = NULL,
            zerodha_user_name = NULL,
            zerodha_token_expires_at = NULL,
            zerodha_connected_at = NULL
        WHERE id = ?
        """,
        (user_id,),
    )


def zerodha_redirect_uri() -> str:
    return url_for("zerodha_callback", _external=True)


def build_zerodha_redirect_state(user_id: int) -> str:
    return zerodha_state_serializer().dumps({"user_id": user_id})


def parse_zerodha_redirect_state(raw_value: str | None) -> int | None:
    if not raw_value:
        return None
    try:
        payload = zerodha_state_serializer().loads(raw_value)
    except Exception:
        return None
    user_id = payload.get("user_id")
    return int(user_id) if user_id else None


def zerodha_login_url(api_key: str, user_id: int) -> str:
    params = urlencode({"v": 3, "api_key": api_key, "redirect_params": f"state={build_zerodha_redirect_state(user_id)}"})
    return f"https://kite.zerodha.com/connect/login?{params}"


def zerodha_api_request(
    endpoint: str,
    *,
    method: str = "GET",
    api_key: str,
    access_token: str | None = None,
    data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = None
    headers = {"X-Kite-Version": "3"}
    if access_token:
        headers["Authorization"] = f"token {api_key}:{access_token}"
    if data is not None:
        payload = urlencode(data).encode("utf-8")
        headers["Content-Type"] = "application/x-www-form-urlencoded"

    request_obj = Request(f"https://api.kite.trade{endpoint}", data=payload, headers=headers, method=method)
    try:
        with urlopen(request_obj, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        try:
            payload_text = exc.read().decode("utf-8")
            error_payload = json.loads(payload_text)
            message = error_payload.get("message") or error_payload.get("error_type") or payload_text
        except Exception:
            message = str(exc)
        raise ValueError(message) from exc
    except URLError as exc:
        raise ValueError(f"Network error while calling Zerodha: {exc.reason}") from exc


def exchange_zerodha_request_token(api_key: str, api_secret: str, request_token: str) -> dict[str, Any]:
    checksum = hashlib.sha256(f"{api_key}{request_token}{api_secret}".encode("utf-8")).hexdigest()
    response = zerodha_api_request(
        "/session/token",
        method="POST",
        api_key=api_key,
        data={"api_key": api_key, "request_token": request_token, "checksum": checksum},
    )
    return response["data"]


def store_zerodha_session(user_id: int, token_data: dict[str, Any]) -> None:
    now = datetime.now()
    expiry = now.replace(hour=6, minute=0, second=0, microsecond=0)
    if expiry <= now:
        expiry += timedelta(days=1)
    execute(
        """
        UPDATE users
        SET
            zerodha_access_token = ?,
            zerodha_public_token = ?,
            zerodha_user_id = ?,
            zerodha_user_name = ?,
            zerodha_token_expires_at = ?,
            zerodha_connected_at = ?
        WHERE id = ?
        """,
        (
            token_data.get("access_token"),
            token_data.get("public_token"),
            token_data.get("user_id"),
            token_data.get("user_name"),
            expiry.strftime("%Y-%m-%d %H:%M:%S"),
            current_timestamp_string(),
            user_id,
        ),
    )


def fetch_zerodha_holdings(api_key: str, access_token: str) -> list[dict[str, Any]]:
    response = zerodha_api_request("/portfolio/holdings", api_key=api_key, access_token=access_token)
    return response.get("data", [])


def sync_zerodha_holdings_to_stocks(user_id: int) -> int:
    user = fetch_one("SELECT * FROM users WHERE id = ?", (user_id,))
    if user is None:
        raise ValueError("No matching user found.")
    api_key = normalize_text(user.get("zerodha_api_key"))
    access_token = normalize_text(user.get("zerodha_access_token"))
    if not api_key or not access_token:
        raise ValueError("Zerodha is not connected for this account.")

    holdings = fetch_zerodha_holdings(api_key, access_token)
    synced_at = current_timestamp_string()
    existing_rows = fetch_all(
        """
        SELECT id, symbol, exchange, isin
        FROM stocks
        WHERE source = ?
        ORDER BY id
        """,
        ("zerodha",),
    )
    existing_by_isin = {
        normalize_text(row.get("isin")): row
        for row in existing_rows
        if normalize_text(row.get("isin"))
    }
    existing_by_symbol_exchange = {
        (normalize_text(row.get("symbol")), normalize_text(row.get("exchange"))): row
        for row in existing_rows
    }
    seen_ids: set[int] = set()

    for holding in holdings:
        symbol = normalize_text(holding.get("tradingsymbol"))
        exchange = normalize_text(holding.get("exchange"))
        isin = normalize_text(holding.get("isin"))
        average_price = as_float(holding.get("average_price"))
        current_price = as_float(holding.get("last_price"))
        quantity = as_float(holding.get("quantity"))

        existing_row = None
        if isin:
            existing_row = existing_by_isin.get(isin)
        if existing_row is None:
            existing_row = existing_by_symbol_exchange.get((symbol, exchange))

        if existing_row is not None:
            execute(
                """
                UPDATE stocks
                SET symbol = ?, exchange = ?, isin = ?, average_price = ?, current_price = ?, quantity = ?, source = ?, last_synced_price_at = ?
                WHERE id = ?
                """,
                (
                    symbol,
                    exchange,
                    isin,
                    average_price,
                    current_price,
                    quantity,
                    "zerodha",
                    synced_at,
                    existing_row["id"],
                ),
            )
            seen_ids.add(existing_row["id"])
            continue

        execute(
            """
            INSERT INTO stocks (symbol, exchange, isin, average_price, current_price, quantity, source, last_synced_price_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                symbol,
                exchange,
                isin,
                average_price,
                current_price,
                quantity,
                "zerodha",
                synced_at,
            ),
        )
        inserted_row = fetch_one(
            """
            SELECT id
            FROM stocks
            WHERE source = ? AND symbol = ? AND exchange = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            ("zerodha", symbol, exchange),
        )
        if inserted_row is not None:
            seen_ids.add(inserted_row["id"])

    stale_ids = [row["id"] for row in existing_rows if row["id"] not in seen_ids]
    for stale_id in stale_ids:
        execute("DELETE FROM stocks WHERE id = ?", (stale_id,))

    execute(
        "UPDATE users SET zerodha_last_sync_at = ? WHERE id = ?",
        (synced_at, user_id),
    )
    return len(holdings)




TEMPLATE_SHEETS: list[tuple[str, list[str]]] = [
    (
        "Users",
        [
            "id",
            "full_name",
            "username",
            "email",
            "password_hash",
            "zerodha_api_key",
            "zerodha_api_secret",
            "zerodha_access_token",
            "zerodha_public_token",
            "zerodha_user_id",
            "zerodha_user_name",
            "zerodha_token_expires_at",
            "zerodha_connected_at",
            "zerodha_last_sync_at",
            "created_at",
        ],
    ),
    ("Banks", ["id", "name"]),
    ("bank_accounts", ["id", "user_id", "bank_id", "balance", "purpose"]),
    (
        "Fixed Deposit",
        ["S.No", "account_id", "Invested", "Interest Rate", "Maturity Date", "Created Date", "TODAY", "Current Amount", "Days To Mature"],
    ),
    ("Stocks", ["S.No", "Symbol", "Exchange", "ISIN", "Average Price", "Current Price", "Quantity", "Source"]),
    ("Mutal Funds", ["S.No", "Fund Name", "Invested", "Returns %", "Monthly SIP", "Current Value"]),
    ("Utility Bills", ["S.No", "Bill Type", "Amount"]),
    ("Loans", ["S.No", "Borrower", "Amount", "Interest Rate"]),
    ("Earnings", ["S.No", "Income Type", "Amount", "Person", "Source"]),
    ("Spending", ["Spending Type", "Amount", "Person", "Recipient"]),
    (
        "Standard_Chits",
        ["S.No", "Organization", "Value", "Duration Months", "Paid Months", "EMI", "Maturity Date", "Started Date", "Current Value", "Note"],
    ),
    ("Variable_Chit", ["Name", "Value", "Months", "Maturity Date", "Total Paid", "Start Date", "Net Value", "EMIs Paid"]),
    ("sneha", ["S.No", "Payment Date", "Amount", "Principal Balance"]),
    ("Overall", ["Label", "Amount", "Note 1", "Note 2"]),
]


def excel_column_name(index: int) -> str:
    name = ""
    current = index
    while current > 0:
        current, remainder = divmod(current - 1, 26)
        name = chr(65 + remainder) + name
    return name


def workbook_xml(sheet_names: list[str]) -> bytes:
    sheets_xml = "".join(
        f'<sheet name="{escape(name)}" sheetId="{idx}" r:id="rId{idx}"/>'
        for idx, name in enumerate(sheet_names, start=1)
    )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f"<sheets>{sheets_xml}</sheets>"
        "</workbook>"
    ).encode("utf-8")


def workbook_rels_xml(sheet_count: int) -> bytes:
    relationships = "".join(
        f'<Relationship Id="rId{idx}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{idx}.xml"/>'
        for idx in range(1, sheet_count + 1)
    )
    relationships += '<Relationship Id="rIdStyles" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        f"{relationships}</Relationships>"
    ).encode("utf-8")


def content_types_xml(sheet_count: int) -> bytes:
    overrides = "".join(
        f'<Override PartName="/xl/worksheets/sheet{idx}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        for idx in range(1, sheet_count + 1)
    )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
        '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
        '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>'
        f"{overrides}</Types>"
    ).encode("utf-8")


def root_rels_xml() -> bytes:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
        '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
        '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>'
        "</Relationships>"
    ).encode("utf-8")


def styles_xml() -> bytes:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<fonts count="1"><font><sz val="11"/><name val="Calibri"/></font></fonts>'
        '<fills count="2"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill></fills>'
        '<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>'
        '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
        '<cellXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/></cellXfs>'
        '<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>'
        "</styleSheet>"
    ).encode("utf-8")


def docprops_app_xml(sheet_names: list[str]) -> bytes:
    titles = "".join(f"<vt:lpstr>{escape(name)}</vt:lpstr>" for name in sheet_names)
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" '
        'xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">'
        "<Application>Microsoft Excel</Application>"
        f"<TitlesOfParts><vt:vector size=\"{len(sheet_names)}\" baseType=\"lpstr\">{titles}</vt:vector></TitlesOfParts>"
        f"<HeadingPairs><vt:vector size=\"2\" baseType=\"variant\"><vt:variant><vt:lpstr>Worksheets</vt:lpstr></vt:variant><vt:variant><vt:i4>{len(sheet_names)}</vt:i4></vt:variant></vt:vector></HeadingPairs>"
        "</Properties>"
    ).encode("utf-8")


def docprops_core_xml() -> bytes:
    timestamp = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
        'xmlns:dc="http://purl.org/dc/elements/1.1/" '
        'xmlns:dcterms="http://purl.org/dc/terms/" '
        'xmlns:dcmitype="http://purl.org/dc/dcmitype/" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
        "<dc:title>Financial Dashboard Template</dc:title>"
        "<dc:creator>Codex</dc:creator>"
        f"<dcterms:created xsi:type=\"dcterms:W3CDTF\">{timestamp}</dcterms:created>"
        f"<dcterms:modified xsi:type=\"dcterms:W3CDTF\">{timestamp}</dcterms:modified>"
        "</cp:coreProperties>"
    ).encode("utf-8")


def sheet_xml(headers: list[str]) -> bytes:
    rows = []
    for row_index, row in enumerate([headers], start=1):
        cells = []
        for col_index, value in enumerate(row, start=1):
            ref = f"{excel_column_name(col_index)}{row_index}"
            cells.append(f'<c r="{ref}" t="inlineStr"><is><t>{escape(value)}</t></is></c>')
        rows.append(f'<row r="{row_index}">{"".join(cells)}</row>')
    dimension = f"A1:{excel_column_name(len(headers))}1" if headers else "A1:A1"
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<dimension ref="{dimension}"/>'
        "<sheetViews><sheetView workbookViewId=\"0\"/></sheetViews>"
        "<sheetFormatPr defaultRowHeight=\"15\"/>"
        f"<sheetData>{''.join(rows)}</sheetData>"
        "</worksheet>"
    ).encode("utf-8")


def build_excel_template() -> BytesIO:
    output = BytesIO()
    sheet_names = [name for name, _headers in TEMPLATE_SHEETS]
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as workbook:
        workbook.writestr("[Content_Types].xml", content_types_xml(len(TEMPLATE_SHEETS)))
        workbook.writestr("_rels/.rels", root_rels_xml())
        workbook.writestr("docProps/app.xml", docprops_app_xml(sheet_names))
        workbook.writestr("docProps/core.xml", docprops_core_xml())
        workbook.writestr("xl/workbook.xml", workbook_xml(sheet_names))
        workbook.writestr("xl/_rels/workbook.xml.rels", workbook_rels_xml(len(TEMPLATE_SHEETS)))
        workbook.writestr("xl/styles.xml", styles_xml())
        for index, (_sheet_name, headers) in enumerate(TEMPLATE_SHEETS, start=1):
            workbook.writestr(f"xl/worksheets/sheet{index}.xml", sheet_xml(headers))
    output.seek(0)
    return output


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
        """
        SELECT
            CONCAT(COALESCE(u.full_name, 'Unknown'), ' / ', COALESCE(b.name, 'Unknown')) AS bank,
            fd.maturity_date,
            fd.current_amount,
            fd.days_to_mature
        FROM fixed_deposits fd
        LEFT JOIN bank_accounts ba ON ba.id = fd.account_id
        LEFT JOIN users u ON u.id = ba.user_id
        LEFT JOIN banks b ON b.id = ba.bank_id
        WHERE fd.days_to_mature BETWEEN 0 AND 120
        ORDER BY fd.days_to_mature ASC
        LIMIT 5
        """
    )
    highest_balances = fetch_all(
        """
        SELECT u.full_name AS account_holder, b.name AS bank_name, ba.balance
        FROM bank_accounts ba
        LEFT JOIN users u ON u.id = ba.user_id
        LEFT JOIN banks b ON b.id = ba.bank_id
        ORDER BY ba.balance DESC
        LIMIT 5
        """
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
    if entity_key == "bank_accounts":
        return {
            "account_holder": normalize_text(form_data.get("account_holder")),
            "bank_name": normalize_text(form_data.get("bank_name")),
            "balance": as_float(form_data.get("balance")),
            "purpose": normalize_text(form_data.get("purpose")),
        }
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
    fetch_one=fetch_one,
    execute=execute,
    as_float=as_float,
    ensure_bank_account_entities=ensure_bank_account_entities,
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
    get_current_user=get_current_user,
    zerodha_login_url=zerodha_login_url,
    zerodha_redirect_uri=zerodha_redirect_uri,
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
        "is_authenticated": is_authenticated(),
        "current_username": session.get("username"),
        "current_full_name": session.get("full_name"),
    }


@app.before_request
def require_login():
    if request.endpoint in AUTH_EXEMPT_ENDPOINTS:
        return None
    if request.endpoint is None or is_authenticated():
        return None
    return redirect(url_for(LOGIN_ENDPOINT, next=request.full_path if request.query_string else request.path))


@app.route("/login", methods=["GET", "POST"])
def login() -> str:
    if is_authenticated():
        return redirect(get_post_login_redirect())

    if request.method == "POST":
        username = normalize_text(request.form.get("username"))
        password = request.form.get("password", "")
        user = verify_login(username, password)
        if user:
            establish_user_session(user)
            flash("Welcome back. You now have access to the dashboard.", "success")
            return redirect(get_post_login_redirect())
        flash("The username or password was incorrect.", "error")

    return render_template("login.html", next_target=get_post_login_redirect())


@app.route("/signup", methods=["GET", "POST"])
def signup() -> str:
    if is_authenticated():
        return redirect(url_for("dashboard"))

    form_values = {
        "full_name": normalize_text(request.form.get("full_name")),
        "username": normalize_text(request.form.get("username")),
        "email": normalize_text(request.form.get("email")).lower(),
    }

    if request.method == "POST":
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not all(form_values.values()) or not password or not confirm_password:
            flash("Please complete every field to create your account.", "error")
        elif password != confirm_password:
            flash("Passwords did not match. Please try again.", "error")
        elif len(password) < 8:
            flash("Use a password with at least 8 characters.", "error")
        elif username_exists(form_values["username"]):
            flash("That username is already taken.", "error")
        elif email_exists(form_values["email"]):
            flash("That email address is already registered.", "error")
        else:
            existing_full_name = get_user_by_full_name(form_values["full_name"])
            if existing_full_name and (
                existing_full_name.get("username")
                or existing_full_name.get("email")
                or existing_full_name.get("password_hash")
            ):
                flash("That full name is already linked to an existing login account.", "error")
                return render_template("signup.html", form_values=form_values)

            create_or_upgrade_auth_user(
                full_name=form_values["full_name"],
                username=form_values["username"],
                email=form_values["email"],
                password=password,
            )
            flash("Account created. You can log in now.", "success")
            return redirect(url_for(LOGIN_ENDPOINT))

    return render_template("signup.html", form_values=form_values)


@app.post("/logout")
def logout():
    session.clear()
    flash("You have been signed out.", "success")
    return redirect(url_for(LOGIN_ENDPOINT))


@app.get("/download-template")
def download_template():
    workbook = build_excel_template()
    return send_file(
        workbook,
        as_attachment=True,
        download_name="financial_dashboard_template.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@app.post("/stocks/zerodha/settings")
def zerodha_settings():
    user = get_current_user()
    if user is None:
        flash("Please log in before configuring Zerodha.", "error")
        return redirect(url_for("login"))

    api_key = normalize_text(request.form.get("api_key"))
    api_secret = normalize_text(request.form.get("api_secret"))
    if not api_key or not api_secret:
        flash("Both Zerodha API key and API secret are required.", "error")
        return redirect(url_for("stocks_page"))

    save_zerodha_credentials(user["id"], api_key, api_secret)
    clear_zerodha_connection(user["id"])
    flash("Zerodha credentials saved. Complete the connect step next.", "success")
    return redirect(url_for("stocks_page"))


@app.get("/stocks/zerodha/connect")
def zerodha_connect():
    user = get_current_user()
    if user is None:
        flash("Please log in before connecting Zerodha.", "error")
        return redirect(url_for("login"))
    api_key = normalize_text(user.get("zerodha_api_key"))
    api_secret = normalize_text(user.get("zerodha_api_secret"))
    if not api_key or not api_secret:
        flash("Save your Zerodha API key and secret first.", "error")
        return redirect(url_for("stocks_page"))
    return redirect(zerodha_login_url(api_key, user["id"]))


@app.get("/stocks/zerodha/callback")
def zerodha_callback():
    user = get_current_user()
    if user is None:
        state_user_id = parse_zerodha_redirect_state(request.args.get("state"))
        if state_user_id:
            user = fetch_one("SELECT * FROM users WHERE id = ?", (state_user_id,))
    if user is None:
        flash("Your app session could not be matched after Zerodha returned. Use the exact same host shown in the redirect URL and try again.", "error")
        return redirect(url_for("login"))
    establish_user_session(user)
    if request.args.get("status") == "error":
        flash(normalize_text(request.args.get("message")) or "Zerodha authorization was cancelled.", "error")
        return redirect(url_for("stocks_page"))

    request_token = normalize_text(request.args.get("request_token"))
    if not request_token:
        flash("Zerodha did not return a request token.", "error")
        return redirect(url_for("stocks_page"))

    try:
        token_data = exchange_zerodha_request_token(
            normalize_text(user.get("zerodha_api_key")),
            normalize_text(user.get("zerodha_api_secret")),
            request_token,
        )
        store_zerodha_session(user["id"], token_data)
    except Exception as exc:
        flash(f"Zerodha connection failed: {exc}", "error")
        return redirect(url_for("stocks_page"))

    flash("Zerodha connected. You can sync holdings now.", "success")
    return redirect(url_for("stocks_page"))


@app.post("/stocks/zerodha/sync")
def zerodha_sync():
    user = get_current_user()
    if user is None:
        flash("Please log in before syncing stocks.", "error")
        return redirect(url_for("login"))

    try:
        synced_count = sync_zerodha_holdings_to_stocks(user["id"])
    except Exception as exc:
        flash(f"Zerodha sync failed: {exc}", "error")
        return redirect(url_for("stocks_page"))

    flash(f"Synced {synced_count} Zerodha stock holding(s) into the dashboard.", "success")
    return redirect(url_for("stocks_page"))


@app.post("/stocks/zerodha/disconnect")
def zerodha_disconnect():
    user = get_current_user()
    if user is None:
        flash("Please log in before disconnecting Zerodha.", "error")
        return redirect(url_for("login"))

    clear_zerodha_connection(user["id"])
    flash("Zerodha access token cleared. Saved API credentials remain in place.", "success")
    return redirect(url_for("stocks_page"))


@app.post("/stocks/manual/clear")
def clear_manual_stock_holdings():
    user = get_current_user()
    if user is None:
        flash("Please log in before clearing manual holdings.", "error")
        return redirect(url_for("login"))

    manual_count = fetch_one(
        "SELECT COUNT(*) AS count FROM stocks WHERE source = ? OR source IS NULL OR TRIM(source) = ''",
        ("manual",),
    )["count"]
    execute(
        "DELETE FROM stocks WHERE source = ? OR source IS NULL OR TRIM(source) = ''",
        ("manual",),
    )
    flash(f"Cleared {manual_count} manual stock holding(s). Zerodha-synced rows were kept.", "success")
    return redirect(url_for("stocks_page"))




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
    if entity_key == "bank_accounts":
        query = """
            SELECT
                ba.id,
                ba.user_id,
                ba.bank_id,
                u.full_name AS account_holder,
                b.name AS bank_name,
                ba.balance,
                ba.purpose
            FROM bank_accounts ba
            LEFT JOIN users u ON u.id = ba.user_id
            LEFT JOIN banks b ON b.id = ba.bank_id
        """
        params: tuple[Any, ...] = ()
        if search:
            query += " WHERE u.full_name LIKE ? OR b.name LIKE ? OR ba.purpose LIKE ?"
            params = (f"%{search}%", f"%{search}%", f"%{search}%")
        query += " ORDER BY ba.id DESC"
        rows = fetch_all(query, params)
    else:
        query = f"SELECT * FROM {entity['table']}"
        params = ()
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
    if entity_key == "bank_accounts":
        user_id, bank_id = ensure_bank_account_entities(values["account_holder"], values["bank_name"])
        execute(
            "UPDATE bank_accounts SET user_id = ?, bank_id = ?, balance = ?, purpose = ? WHERE id = ?",
            (user_id, bank_id, values["balance"], values["purpose"], row_id),
        )
    else:
        assignments = ", ".join(f"{name} = ?" for name in values)
        execute(
            f"UPDATE {entity['table']} SET {assignments} WHERE id = ?",
            tuple(values.values()) + (row_id,),
        )
    if entity_key == "bank_accounts":
        sync_bank_account_reference_data()
    flash(f"{record_label(entity_key)} row updated.", "success")
    return redirect(url_for("entity_list", entity_key=entity_key))


@app.route("/entity/<entity_key>/new", methods=["GET", "POST"])
def entity_create(entity_key: str) -> str:
    entity = ENTITY_CONFIG.get(entity_key)
    if entity is None:
        abort(404)
    if request.method == "POST":
        values = serialize_form(entity_key, request.form)
        if entity_key == "bank_accounts":
            user_id, bank_id = ensure_bank_account_entities(values["account_holder"], values["bank_name"])
            execute(
                "INSERT INTO bank_accounts (user_id, bank_id, balance, purpose) VALUES (?, ?, ?, ?)",
                (user_id, bank_id, values["balance"], values["purpose"]),
            )
        else:
            columns = list(values.keys())
            execute(
                f"INSERT INTO {entity['table']} ({', '.join(columns)}) VALUES ({', '.join('?' for _ in columns)})",
                tuple(values[column] for column in columns),
            )
        if entity_key == "bank_accounts":
            sync_bank_account_reference_data()
        flash(f"{record_label(entity_key)} record added successfully.", "success")
        return redirect(url_for("entity_list", entity_key=entity_key))
    return render_template("entity_form.html", entity_key=entity_key, entity=entity, row={})


@app.route("/entity/<entity_key>/<int:row_id>/edit", methods=["GET", "POST"])
def entity_edit(entity_key: str, row_id: int) -> str:
    entity = ENTITY_CONFIG.get(entity_key)
    if entity is None:
        abort(404)
    if entity_key == "bank_accounts":
        row = fetch_one(
            """
            SELECT
                ba.id,
                ba.user_id,
                ba.bank_id,
                u.full_name AS account_holder,
                b.name AS bank_name,
                ba.balance,
                ba.purpose
            FROM bank_accounts ba
            LEFT JOIN users u ON u.id = ba.user_id
            LEFT JOIN banks b ON b.id = ba.bank_id
            WHERE ba.id = ?
            """,
            (row_id,),
        )
    else:
        row = fetch_one(f"SELECT * FROM {entity['table']} WHERE id = ?", (row_id,))
    if row is None:
        abort(404)
    if request.method == "POST":
        values = serialize_form(entity_key, request.form)
        if entity_key == "bank_accounts":
            user_id, bank_id = ensure_bank_account_entities(values["account_holder"], values["bank_name"])
            execute(
                "UPDATE bank_accounts SET user_id = ?, bank_id = ?, balance = ?, purpose = ? WHERE id = ?",
                (user_id, bank_id, values["balance"], values["purpose"], row_id),
            )
        else:
            assignments = ", ".join(f"{name} = ?" for name in values)
            execute(
                f"UPDATE {entity['table']} SET {assignments} WHERE id = ?",
                tuple(values.values()) + (row_id,),
            )
        if entity_key == "bank_accounts":
            sync_bank_account_reference_data()
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
