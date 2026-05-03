from __future__ import annotations

import hashlib
import csv
import json
import threading
import zipfile
import os
from datetime import date, datetime, timedelta
from io import BytesIO, StringIO
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
    from .routes.workspaces import (
        compute_fixed_deposit_current_amount,
        compute_fixed_deposit_days_to_mature,
    )
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
    from routes.workspaces import (
        compute_fixed_deposit_current_amount,
        compute_fixed_deposit_days_to_mature,
    )


app = Flask(__name__)
app.secret_key = "financial-dashboard-dev"

APP_ROOT = Path(__file__).resolve().parent
WORKBOOK_PATH = Path(os.getenv("WORKBOOK_PATH", APP_ROOT / "Income.xlsx"))
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
            {"name": "account_id", "label": "Account (holder · bank)", "type": "number", "step": "1"},
            {"name": "invested", "label": "Invested", "type": "number", "step": "0.01"},
            {"name": "interest_rate", "label": "Interest Rate %", "type": "number", "step": "0.01"},
            {"name": "maturity_date", "label": "Maturity Date", "type": "date"},
            {"name": "created_date", "label": "Created Date", "type": "date"},
            {"name": "current_amount", "label": "Current Amount", "type": "number", "step": "0.01"},
            {"name": "days_to_mature", "label": "Days To Mature", "type": "number", "step": "1", "read_only": True},
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
            {"name": "returns_pct", "label": "Returns %", "type": "number", "step": "0.01"},
            {"name": "quantity", "label": "Quantity", "type": "number", "step": "1"},
            {"name": "last_synced_price_at", "label": "Price Synced At", "type": "text"},
        ],
    },
    "mutual_funds": {
        "title": "Mutual Funds",
        "description": "SIP and total current value by fund.",
        "table": "mutual_funds",
        "columns": [
            {"name": "fund_name", "label": "Fund Name", "type": "text"},
            {"name": "current_value", "label": "Current Value", "type": "number", "step": "0.01"},
            {"name": "returns_pct", "label": "Returns %", "type": "number", "step": "0.01"},
            {"name": "units", "label": "Units", "type": "number", "step": "0.01"},
            {"name": "average_nav", "label": "Average NAV", "type": "number", "step": "0.0001"},
            {"name": "latest_nav", "label": "Latest NAV", "type": "number", "step": "0.0001"},
            {"name": "sip", "label": "Monthly SIP", "type": "number", "step": "0.01"},
            {"name": "nav_synced_at", "label": "NAV Synced At", "type": "text"},
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
    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "teja@4795")
    MYSQL_DB = os.getenv("MYSQL_DB", "teja")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))


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


def compute_stock_returns_pct(row: dict[str, Any]) -> float:
    average = as_float(row.get("average_price"))
    current = as_float(row.get("current_price"))
    if average:
        return ((current - average) / average) * 100
    return 0.0


def compute_mutual_fund_returns_pct(row: dict[str, Any]) -> float:
    average_nav = as_float(row.get("average_nav"))
    units = as_float(row.get("units"))
    latest_nav = as_float(row.get("latest_nav"))
    invested_value = as_float(row.get("amount_invested")) if row.get("amount_invested") is not None else 0.0
    invested = invested_value if invested_value else average_nav * units
    current_value_source = row.get("current_value")
    if current_value_source is not None:
        current_value = as_float(current_value_source)
    else:
        current_value = latest_nav * units
    if invested:
        return ((current_value - invested) / invested) * 100
    return 0.0




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
        port=Config.MYSQL_PORT,
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


_JPM_PRICE_CACHE: dict[str, Any] = {
    "price": None,
    "rate": None,
    "expires_at": datetime.min,
}


def _fetch_jpm_inr_price() -> tuple[float, float] | None:
    cache = _JPM_PRICE_CACHE
    now = datetime.now()
    expires_at = cache["expires_at"]
    if expires_at and expires_at > now and cache["price"] is not None and cache["rate"] is not None:
        return cache["price"], cache["rate"]
    try:
        import yfinance as yf
    except ImportError:
        return None

    price_inr = None
    usd_inr_rate = None
    for attempt in range(3):
        try:
            ticker = yf.Ticker("JPM")
            history = ticker.history(period="1d")
            if history.empty:
                raise ValueError("JPM history empty")
            close_usd = history["Close"].iloc[-1]
            fx_ticker = yf.Ticker("INR=X")
            fx_history = fx_ticker.history(period="1d")
            if fx_history.empty:
                raise ValueError("USDINR history empty")
            usd_inr_rate = fx_history["Close"].iloc[-1]
            price_inr = close_usd * usd_inr_rate
            break
        except Exception:
            if attempt < 2:
                continue
            return None

    cache["price"] = price_inr
    cache["rate"] = usd_inr_rate
    cache["expires_at"] = now + timedelta(minutes=15)
    return price_inr, usd_inr_rate


def _update_jpm_stock(price_inr: float, usd_inr_rate: float) -> int:
    rows = fetch_all("SELECT id, average_price FROM stocks WHERE UPPER(symbol) = 'JPM'")
    if not rows:
        return 0
    timestamp = current_timestamp_string()
    updated = 0
    for row in rows:
        execute(
            "UPDATE stocks SET current_price = ?, last_synced_price_at = ? WHERE id = ?",
            (price_inr, timestamp, row["id"]),
        )
        updated += 1
    return updated


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


def _format_workbook_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")
    return str(value)


def _sheet_xml_with_rows(headers: list[str], rows: list[list[Any]]) -> bytes:
    data_rows = [headers] + rows
    rows_xml = []
    for row_index, row in enumerate(data_rows, start=1):
        cells = []
        for col_index, value in enumerate(row, start=1):
            ref = f"{excel_column_name(col_index)}{row_index}"
            text = escape(_format_workbook_value(value))
            cells.append(f'<c r="{ref}" t="inlineStr"><is><t>{text}</t></is></c>')
        rows_xml.append(f'<row r="{row_index}">{"".join(cells)}</row>')
    dimension = f"A1:{excel_column_name(len(headers))}{len(data_rows)}" if headers else "A1:A1"
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<dimension ref="{dimension}"/>'
        "<sheetViews><sheetView workbookViewId=\"0\"/></sheetViews>"
        "<sheetFormatPr defaultRowHeight=\"15\"/>"
        f"<sheetData>{''.join(rows_xml)}</sheetData>"
        "</worksheet>"
    ).encode("utf-8")


def build_workbook_from_data(sheets: list[tuple[str, list[str], list[list[Any]]]]) -> BytesIO:
    output = BytesIO()
    sheet_names = [name for name, _, _ in sheets]
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as workbook:
        workbook.writestr("[Content_Types].xml", content_types_xml(len(sheets)))
        workbook.writestr("_rels/.rels", root_rels_xml())
        workbook.writestr("docProps/app.xml", docprops_app_xml(sheet_names))
        workbook.writestr("docProps/core.xml", docprops_core_xml())
        workbook.writestr("xl/workbook.xml", workbook_xml(sheet_names))
        workbook.writestr("xl/_rels/workbook.xml.rels", workbook_rels_xml(len(sheets)))
        workbook.writestr("xl/styles.xml", styles_xml())
        for index, (_sheet_name, headers, rows) in enumerate(sheets, start=1):
            workbook.writestr(f"xl/worksheets/sheet{index}.xml", _sheet_xml_with_rows(headers, rows))
    output.seek(0)
    return output


def build_workbook_from_db() -> BytesIO:
    today = datetime.now().date()

    def rows_from_query(columns: list[str], query: str) -> list[list[Any]]:
        data = fetch_all(query)
        return [[row.get(col) for col in columns] for row in data]

    user_columns = TEMPLATE_SHEETS[0][1]
    user_rows = rows_from_query(
        user_columns,
        """SELECT id, full_name, username, email, password_hash, zerodha_api_key, zerodha_api_secret,
           zerodha_access_token, zerodha_public_token, zerodha_user_id, zerodha_user_name, zerodha_token_expires_at,
           zerodha_connected_at, zerodha_last_sync_at, created_at FROM users ORDER BY id""",
    )
    bank_columns = TEMPLATE_SHEETS[1][1]
    bank_rows = rows_from_query(bank_columns, "SELECT id, name FROM banks ORDER BY id")
    bank_account_columns = TEMPLATE_SHEETS[2][1]
    bank_account_rows = rows_from_query(
        bank_account_columns, "SELECT id, user_id, bank_id, balance, purpose FROM bank_accounts ORDER BY id"
    )

    fd_headers = TEMPLATE_SHEETS[3][1]
    fd_rows_raw = fetch_all("SELECT * FROM fixed_deposits ORDER BY id")
    fd_rows_data: list[list[Any]] = []
    for idx, row in enumerate(fd_rows_raw, start=1):
        current_amount = compute_fixed_deposit_current_amount(row, as_float, today)
        days = compute_fixed_deposit_days_to_mature(row, today)
        fd_rows_data.append(
            [
                idx,
                row.get("account_id"),
                row.get("invested"),
                row.get("interest_rate"),
                row.get("maturity_date"),
                row.get("created_date"),
                today.isoformat(),
                current_amount,
                days if days is not None else "",
            ]
        )

    stock_headers = TEMPLATE_SHEETS[4][1]
    stock_rows_raw = fetch_all(
        "SELECT symbol, exchange, isin, average_price, current_price, quantity, source FROM stocks ORDER BY id"
    )
    stock_rows_data = []
    for idx, row in enumerate(stock_rows_raw, start=1):
        stock_rows_data.append(
            [
                idx,
                row.get("symbol"),
                row.get("exchange"),
                row.get("isin"),
                row.get("average_price"),
                row.get("current_price"),
                row.get("quantity"),
                row.get("source"),
            ]
        )

    mf_headers = TEMPLATE_SHEETS[5][1]
    mf_rows_raw = fetch_all("SELECT * FROM mutual_funds ORDER BY id")
    mf_rows_data = []
    for idx, row in enumerate(mf_rows_raw, start=1):
        latest_nav = as_float(row.get("latest_nav"))
        units = as_float(row.get("units"))
        row["current_value"] = latest_nav * units
        returns_pct = compute_mutual_fund_returns_pct(row)
        mf_rows_data.append([idx, row.get("fund_name"), row.get("invested"), returns_pct, row.get("sip"), row["current_value"]])

    utility_headers = TEMPLATE_SHEETS[6][1]
    utility_rows = rows_from_query(utility_headers[1:], "SELECT bill_type, amount FROM utility_bills ORDER BY id")
    utility_rows = [[idx + 1, *row] for idx, row in enumerate(utility_rows)]

    loan_headers = TEMPLATE_SHEETS[7][1]
    loan_rows_raw = fetch_all("SELECT borrower, amount, interest_rate FROM loans ORDER BY id")
    loan_rows = [[idx + 1, row.get("borrower"), row.get("amount"), row.get("interest_rate")] for idx, row in enumerate(loan_rows_raw)]

    earnings_headers = TEMPLATE_SHEETS[8][1]
    earnings_rows_raw = fetch_all("SELECT income_type, amount, person, source FROM earnings ORDER BY id")
    earnings_rows = [[idx + 1, *[row.get(col.lower()) for col in earnings_headers[1:]]] for idx, row in enumerate(earnings_rows_raw)]

    spending_headers = TEMPLATE_SHEETS[9][1]
    spending_rows_raw = fetch_all("SELECT spending_type, amount, person, recipient FROM spending ORDER BY id")
    spending_rows = [[row.get("spending_type"), row.get("amount"), row.get("person"), row.get("recipient")] for row in spending_rows_raw]

    std_headers = TEMPLATE_SHEETS[10][1]
    std_rows_raw = fetch_all("SELECT organization, value, duration_months, paid_months, emi, maturity_date, started_date, current_value, note FROM standard_chits ORDER BY id")
    standard_rows = []
    for idx, row in enumerate(std_rows_raw, start=1):
        standard_rows.append(
            [
                idx,
                row.get("organization"),
                row.get("value"),
                row.get("duration_months"),
                row.get("paid_months"),
                row.get("emi"),
                row.get("maturity_date"),
                row.get("started_date"),
                row.get("current_value"),
                row.get("note"),
            ]
        )

    variable_headers = TEMPLATE_SHEETS[11][1]
    variable_rows_raw = fetch_all("SELECT name, value, months, maturity_date, total_paid, start_date, net_value, emi_paid FROM variable_chits ORDER BY id")
    variable_rows = [[row.get("name"), row.get("value"), row.get("months"), row.get("maturity_date"), row.get("total_paid"), row.get("start_date"), row.get("net_value"), row.get("emi_paid")] for row in variable_rows_raw]

    sneha_headers = TEMPLATE_SHEETS[12][1]
    sneha_rows_raw = fetch_all("SELECT payment_date, amount, principal_balance FROM sneha_payments ORDER BY id")
    sneha_rows = [[idx + 1, row.get("payment_date"), row.get("amount"), row.get("principal_balance")] for idx, row in enumerate(sneha_rows_raw)]

    overall_headers = TEMPLATE_SHEETS[13][1]
    overall_rows_raw = fetch_all("SELECT label, amount, note FROM overall_assets ORDER BY id")
    overall_rows = [[row.get("label"), row.get("amount"), row.get("note"), ""] for row in overall_rows_raw]

    sheets_data = [
        ("Users", user_columns, user_rows),
        ("Banks", bank_columns, bank_rows),
        ("bank_accounts", bank_account_columns, bank_account_rows),
        ("Fixed Deposit", fd_headers, fd_rows_data),
        ("Stocks", stock_headers, stock_rows_data),
        ("Mutal Funds", mf_headers, mf_rows_data),
        ("Utility Bills", utility_headers, utility_rows),
        ("Loans", loan_headers, loan_rows),
        ("Earnings", earnings_headers, earnings_rows),
        ("Spending", spending_headers, spending_rows),
        ("Standard_Chits", std_headers, standard_rows),
        ("Variable_Chit", variable_headers, variable_rows),
        ("sneha", sneha_headers, sneha_rows),
        ("Overall", overall_headers, overall_rows),
    ]
    return build_workbook_from_data(sheets_data)


def build_dashboard_metrics() -> dict[str, Any]:
    today = datetime.now().date()
    fd_rows = fetch_all("SELECT * FROM fixed_deposits")
    fd_total = sum(compute_fixed_deposit_current_amount(row, as_float, today) for row in fd_rows)
    totals = {
        "bank": fetch_one("SELECT COALESCE(SUM(balance), 0) AS total FROM bank_accounts")["total"],
        "fd": fd_total,
        "stocks": fetch_one("SELECT COALESCE(SUM(current_price * quantity), 0) AS total FROM stocks")["total"],
        "mutual_funds": fetch_one("SELECT COALESCE(SUM(latest_nav * units), 0) AS total FROM mutual_funds")[
            "total"
        ],
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
            fd.*,
            CONCAT(COALESCE(u.full_name, 'Unknown'), ' / ', COALESCE(b.name, 'Unknown')) AS bank,
            ba.purpose AS account_purpose
        FROM fixed_deposits fd
        LEFT JOIN bank_accounts ba ON ba.id = fd.account_id
        LEFT JOIN users u ON u.id = ba.user_id
        LEFT JOIN banks b ON b.id = ba.bank_id
        WHERE fd.maturity_date IS NOT NULL
          AND DATEDIFF(fd.maturity_date, CURDATE()) BETWEEN 0 AND 120
        ORDER BY fd.maturity_date ASC
        LIMIT 5
        """
    )
    for row in upcoming_fds:
        row["current_amount"] = compute_fixed_deposit_current_amount(row, as_float, today)
        row["days_to_mature"] = compute_fixed_deposit_days_to_mature(row, today)
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


def percent_of(part: float, whole: float) -> float:
    return (part / whole * 100) if whole else 0.0


def normalize_date_value(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def build_report_rows() -> dict[str, list[dict[str, Any]]]:
    today = datetime.now().date()
    fixed_deposits = fetch_all(
        """
        SELECT
            fd.*,
            u.full_name AS account_holder,
            b.name AS bank_name,
            ba.purpose AS account_purpose
        FROM fixed_deposits fd
        LEFT JOIN bank_accounts ba ON ba.id = fd.account_id
        LEFT JOIN users u ON u.id = ba.user_id
        LEFT JOIN banks b ON b.id = ba.bank_id
        ORDER BY fd.maturity_date ASC, fd.invested DESC
        """
    )
    for row in fixed_deposits:
        row["current_amount"] = compute_fixed_deposit_current_amount(row, as_float, today)
        row["days_to_mature"] = compute_fixed_deposit_days_to_mature(row, today)

    stocks = fetch_all(
        """
        SELECT symbol, exchange, average_price, current_price, quantity, source, last_synced_price_at
        FROM stocks
        ORDER BY current_price * quantity DESC, symbol ASC
        """
    )
    for row in stocks:
        row["invested_value"] = as_float(row.get("average_price")) * as_float(row.get("quantity"))
        row["market_value"] = as_float(row.get("current_price")) * as_float(row.get("quantity"))
        row["pnl"] = row["market_value"] - row["invested_value"]
        row["returns_pct"] = percent_of(row["pnl"], row["invested_value"])

    mutual_funds = fetch_all("SELECT * FROM mutual_funds ORDER BY latest_nav * units DESC, fund_name ASC")
    for row in mutual_funds:
        invested_value = as_float(row.get("average_nav")) * as_float(row.get("units"))
        current_value = as_float(row.get("latest_nav")) * as_float(row.get("units"))
        row["invested_value"] = invested_value
        row["current_value"] = current_value
        row["pnl"] = current_value - invested_value
        row["returns_pct"] = percent_of(row["pnl"], invested_value)

    spending = fetch_all("SELECT spending_type AS label, person, recipient, amount FROM spending ORDER BY amount DESC")
    utilities = fetch_all("SELECT bill_type AS label, '' AS person, 'Utility' AS recipient, amount FROM utility_bills ORDER BY amount DESC")

    return {
        "bank_accounts": fetch_all(
            """
            SELECT u.full_name AS account_holder, b.name AS bank_name, ba.balance, ba.purpose
            FROM bank_accounts ba
            LEFT JOIN users u ON u.id = ba.user_id
            LEFT JOIN banks b ON b.id = ba.bank_id
            ORDER BY ba.balance DESC
            """
        ),
        "fixed_deposits": fixed_deposits,
        "stocks": stocks,
        "mutual_funds": mutual_funds,
        "earnings": fetch_all("SELECT income_type, amount, person, source FROM earnings ORDER BY amount DESC"),
        "outflows": [*spending, *utilities],
        "loans_receivable": fetch_all("SELECT borrower, amount, interest_rate FROM loans WHERE amount > 0 ORDER BY amount DESC"),
        "loan_obligations": fetch_all("SELECT borrower, ABS(amount) AS amount, interest_rate FROM loans WHERE amount < 0 ORDER BY ABS(amount) DESC"),
        "chits": fetch_all(
            """
            SELECT organization AS label, current_value AS amount, maturity_date, emi, note
            FROM standard_chits
            UNION ALL
            SELECT name AS label, net_value AS amount, maturity_date, total_paid AS emi, '' AS note
            FROM variable_chits
            ORDER BY amount DESC
            """
        ),
        "variable_chit_payments": fetch_all(
            "SELECT emi_no, amount, payment_date, actual_paid FROM variable_chit_payments ORDER BY payment_date ASC, emi_no ASC"
        ),
        "sneha_payments": fetch_all(
            "SELECT payment_date, amount, principal_balance FROM sneha_payments ORDER BY payment_date ASC, id ASC"
        ),
        "overall_assets": fetch_all("SELECT label, amount, note FROM overall_assets ORDER BY amount DESC"),
    }


def group_amount(rows: list[dict[str, Any]], key: str, amount_key: str = "amount") -> list[dict[str, Any]]:
    totals: dict[str, float] = {}
    for row in rows:
        label = normalize_text(row.get(key)) or "Unassigned"
        totals[label] = totals.get(label, 0.0) + as_float(row.get(amount_key))
    return [
        {"label": label, "amount": amount}
        for label, amount in sorted(totals.items(), key=lambda item: item[1], reverse=True)
    ]


def build_reports_context() -> dict[str, Any]:
    metrics = build_dashboard_metrics()
    rows = build_report_rows()
    investments = [*rows["stocks"], *rows["mutual_funds"]]
    invested_total = sum(as_float(row.get("invested_value")) for row in investments)
    market_total = sum(as_float(row.get("market_value", row.get("current_value"))) for row in investments)
    outflow_total = sum(as_float(row.get("amount")) for row in rows["outflows"])
    savings_rate = percent_of(metrics["monthly_surplus"], metrics["monthly_income"])
    near_maturities = [
        row for row in rows["fixed_deposits"]
        if row.get("days_to_mature") is not None and 0 <= row["days_to_mature"] <= 180
    ]
    concentration = sorted(metrics["asset_mix"], key=lambda item: item["amount"], reverse=True)

    report_notes = []
    if concentration:
        report_notes.append(
            f"{concentration[0]['label']} is the largest asset class at {percent_of(concentration[0]['amount'], metrics['asset_total']):.1f}% of tracked assets."
        )
    if savings_rate >= 0:
        report_notes.append(f"Monthly surplus is {savings_rate:.1f}% of monthly income.")
    else:
        report_notes.append(f"Monthly outflow exceeds income by {format_currency(abs(metrics['monthly_surplus']))}.")
    if near_maturities:
        report_notes.append(f"{len(near_maturities)} fixed deposit(s) mature within the next 180 days.")
    if market_total or invested_total:
        report_notes.append(f"Market investments show {format_currency(market_total - invested_total)} total P&L.")

    chart_colors = ["#0b6e4f", "#c26d2b", "#355c7d", "#7c3f58", "#4f6f52", "#b54708", "#475569"]
    allocation = [
        {**item, "share": percent_of(item["amount"], metrics["asset_total"]), "color": chart_colors[index % len(chart_colors)]}
        for index, item in enumerate(metrics["asset_mix"])
    ]
    cursor = 0.0
    donut_stops = []
    for item in allocation:
        start = cursor
        cursor += item["share"]
        donut_stops.append(f"{item['color']} {start:.2f}% {cursor:.2f}%")
    asset_donut_style = ", ".join(donut_stops) if donut_stops else "#ddd 0% 100%"
    investment_rows = sorted(
        [
            {"name": row["symbol"], "type": "Stock", **row}
            for row in rows["stocks"]
        ]
        + [
            {"name": row["fund_name"], "type": "Mutual Fund", **row}
            for row in rows["mutual_funds"]
        ],
        key=lambda row: abs(as_float(row.get("pnl"))),
        reverse=True,
    )
    max_investment_move = max((abs(as_float(row.get("pnl"))) for row in investment_rows), default=1) or 1
    max_outflow = max((as_float(row.get("amount")) for row in rows["outflows"]), default=1) or 1
    asset_total = as_float(metrics["asset_total"])
    bank_total = next((as_float(item["amount"]) for item in allocation if item["label"] == "Bank"), 0.0)
    fd_total = next((as_float(item["amount"]) for item in allocation if item["label"] == "Fixed Deposits"), 0.0)
    liquid_total = bank_total + fd_total
    liquidity_months = (liquid_total / outflow_total) if outflow_total else 0.0
    income_vs_outflow = [
        {"label": "Income", "amount": as_float(metrics["monthly_income"]), "color": "#0b6e4f"},
        {"label": "Outflow", "amount": as_float(metrics["monthly_spend"]), "color": "#c26d2b"},
        {"label": "Surplus", "amount": as_float(metrics["monthly_surplus"]), "color": "#355c7d"},
    ]
    max_cashflow = max((abs(item["amount"]) for item in income_vs_outflow), default=1) or 1
    maturity_buckets = [
        {"label": "0-30 days", "amount": 0.0, "count": 0},
        {"label": "31-90 days", "amount": 0.0, "count": 0},
        {"label": "91-180 days", "amount": 0.0, "count": 0},
        {"label": "180+ days", "amount": 0.0, "count": 0},
    ]
    for row in rows["fixed_deposits"]:
        days = row.get("days_to_mature")
        if days is None:
            continue
        if days <= 30:
            bucket = maturity_buckets[0]
        elif days <= 90:
            bucket = maturity_buckets[1]
        elif days <= 180:
            bucket = maturity_buckets[2]
        else:
            bucket = maturity_buckets[3]
        bucket["amount"] += as_float(row.get("current_amount"))
        bucket["count"] += 1
    max_maturity_bucket = max((bucket["amount"] for bucket in maturity_buckets), default=1) or 1
    fd_liquidity_windows = {
        "30": sum(as_float(row.get("current_amount")) for row in rows["fixed_deposits"] if row.get("days_to_mature") is not None and row["days_to_mature"] <= 30),
        "90": sum(as_float(row.get("current_amount")) for row in rows["fixed_deposits"] if row.get("days_to_mature") is not None and row["days_to_mature"] <= 90),
        "180": sum(as_float(row.get("current_amount")) for row in rows["fixed_deposits"] if row.get("days_to_mature") is not None and row["days_to_mature"] <= 180),
        "365": sum(as_float(row.get("current_amount")) for row in rows["fixed_deposits"] if row.get("days_to_mature") is not None and row["days_to_mature"] <= 365),
    }
    monthly_income = as_float(metrics["monthly_income"])
    monthly_spend = as_float(metrics["monthly_spend"])
    annual_income = monthly_income * 12
    annual_outflow = monthly_spend * 12
    annual_sip = sum(as_float(row.get("sip")) for row in rows["mutual_funds"]) * 12
    annual_utility = sum(
        as_float(row.get("amount"))
        for row in rows["outflows"]
        if normalize_text(row.get("recipient")).lower() == "utility"
    ) * 12
    annual_planned_spend = (monthly_spend * 12) - annual_utility
    loans_receivable_total = sum(as_float(row.get("amount")) for row in rows["loans_receivable"])
    loan_obligation_total = sum(as_float(row.get("amount")) for row in rows["loan_obligations"])
    one_pct_market_move = market_total * 0.01
    annual_surplus = as_float(metrics["monthly_surplus"]) * 12
    projected_net_worth_12m = as_float(metrics["net_worth"]) + annual_surplus
    next_events = []
    today = datetime.now().date()
    for row in rows["fixed_deposits"]:
        event_date = normalize_date_value(row.get("maturity_date"))
        if event_date and event_date >= today:
            next_events.append(
                {
                    "date": event_date,
                    "label": f"FD: {row.get('bank_name') or 'Unknown bank'}",
                    "amount": as_float(row.get("current_amount")),
                    "type": "Fixed Deposit",
                }
            )
    for row in rows["chits"]:
        event_date = normalize_date_value(row.get("maturity_date"))
        if event_date and event_date >= today:
            next_events.append(
                {
                    "date": event_date,
                    "label": f"Chit: {row.get('label') or 'Unnamed'}",
                    "amount": as_float(row.get("amount")),
                    "type": "Chit",
                }
            )
    for row in rows["variable_chit_payments"]:
        event_date = normalize_date_value(row.get("payment_date"))
        if event_date and event_date >= today and row.get("actual_paid") is None:
            next_events.append(
                {
                    "date": event_date,
                    "label": f"Variable chit EMI {row.get('emi_no') or ''}".strip(),
                    "amount": as_float(row.get("amount")),
                    "type": "Chit Payment",
                }
            )
    for row in rows["sneha_payments"]:
        event_date = normalize_date_value(row.get("payment_date"))
        if event_date and event_date >= today:
            next_events.append(
                {
                    "date": event_date,
                    "label": "Sneha payment",
                    "amount": as_float(row.get("amount")),
                    "type": "Payment",
                }
            )
    next_events = sorted(next_events, key=lambda item: item["date"])
    largest_future_amount = max((event["amount"] for event in next_events), default=1) or 1
    next_event = next_events[0] if next_events else None
    future_cards = [
        {
            "label": "12M Income Run-Rate",
            "value": format_currency(annual_income),
            "note": "Current monthly income annualized from the earnings section.",
        },
        {
            "label": "12M Outflow Run-Rate",
            "value": format_currency(annual_outflow),
            "note": "Spending and utility bills annualized from current rows.",
        },
        {
            "label": "12M SIP Commitment",
            "value": format_currency(annual_sip),
            "note": "Mutual fund SIP load projected over the next 12 months.",
        },
        {
            "label": "Projected Net Worth",
            "value": format_currency(projected_net_worth_12m),
            "note": "Today net worth plus the current 12-month surplus run-rate.",
        },
        {
            "label": "Next Event",
            "value": next_event["date"].isoformat() if next_event else "No date",
            "note": f"{next_event['label']} for {format_currency(next_event['amount'])}." if next_event else "No upcoming dated maturity or payment found.",
        },
    ]
    future_focus = [
        {"label": "Income", "amount": annual_income, "note": "12M earning run-rate"},
        {"label": "Spending", "amount": annual_planned_spend, "note": "12M planned spend run-rate"},
        {"label": "Utilities", "amount": annual_utility, "note": "12M utility run-rate"},
        {"label": "SIPs", "amount": annual_sip, "note": "12M mutual fund contribution"},
        {"label": "Receivables", "amount": loans_receivable_total, "note": "Capital expected back"},
        {"label": "Obligations", "amount": loan_obligation_total, "note": "Capital owed"},
        {"label": "1% Market Move", "amount": one_pct_market_move, "note": "Sensitivity on stocks and funds"},
    ]
    largest_future_focus = max((abs(item["amount"]) for item in future_focus), default=1) or 1
    attention_cards = [
        {
            "label": "Liquidity Runway",
            "value": f"{liquidity_months:.1f} months",
            "note": f"Bank and FD coverage against current monthly outflow.",
        },
        {
            "label": "Asset Concentration",
            "value": f"{percent_of(concentration[0]['amount'], asset_total):.1f}%" if concentration else "0.0%",
            "note": f"{concentration[0]['label']} is the largest allocation." if concentration else "No allocation data yet.",
        },
        {
            "label": "Near Maturities",
            "value": str(len(near_maturities)),
            "note": "Fixed deposits maturing within 180 days.",
        },
        {
            "label": "Outflow Load",
            "value": f"{percent_of(metrics['monthly_spend'], metrics['monthly_income']):.1f}%",
            "note": "Monthly outflow as a share of income.",
        },
    ]

    return {
        "generated_on": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "metrics": metrics,
        "rows": rows,
        "asset_allocation": allocation,
        "asset_donut_style": asset_donut_style,
        "income_by_person": group_amount(rows["earnings"], "person"),
        "income_by_type": group_amount(rows["earnings"], "income_type"),
        "outflow_by_person": group_amount(rows["outflows"], "person"),
        "outflow_by_type": group_amount(rows["outflows"], "label"),
        "investment_rows": investment_rows,
        "max_investment_move": max_investment_move,
        "max_outflow": max_outflow,
        "income_vs_outflow": income_vs_outflow,
        "max_cashflow": max_cashflow,
        "liquid_total": liquid_total,
        "liquidity_months": liquidity_months,
        "maturity_buckets": maturity_buckets,
        "max_maturity_bucket": max_maturity_bucket,
        "attention_cards": attention_cards,
        "future_cards": future_cards,
        "future_events": next_events[:10],
        "largest_future_amount": largest_future_amount,
        "future_focus": future_focus,
        "largest_future_focus": largest_future_focus,
        "fd_liquidity_windows": fd_liquidity_windows,
        "annual_surplus": annual_surplus,
        "annual_income": annual_income,
        "annual_outflow": annual_outflow,
        "annual_sip": annual_sip,
        "annual_utility": annual_utility,
        "annual_planned_spend": annual_planned_spend,
        "one_pct_market_move": one_pct_market_move,
        "projected_net_worth_12m": projected_net_worth_12m,
        "investment_summary": {
            "invested_total": invested_total,
            "market_total": market_total,
            "pnl": market_total - invested_total,
            "returns_pct": percent_of(market_total - invested_total, invested_total),
        },
        "outflow_total": outflow_total,
        "savings_rate": savings_rate,
        "near_maturities": near_maturities[:10],
        "report_notes": report_notes,
    }


def build_reports_csv(context: dict[str, Any]) -> BytesIO:
    text_buffer = StringIO()
    writer = csv.writer(text_buffer)
    writer.writerow(["Report", "Generated", context["generated_on"]])
    writer.writerow([])
    writer.writerow(["Metric", "Value"])
    for label, value in [
        ("Net Worth", context["metrics"]["net_worth"]),
        ("Asset Base", context["metrics"]["asset_total"]),
        ("Monthly Income", context["metrics"]["monthly_income"]),
        ("Monthly Outflow", context["metrics"]["monthly_spend"]),
        ("Monthly Surplus", context["metrics"]["monthly_surplus"]),
        ("Loan Obligations", context["metrics"]["loan_obligations"]),
    ]:
        writer.writerow([label, value])
    writer.writerow([])
    writer.writerow(["Asset Class", "Amount", "Share %"])
    for item in context["asset_allocation"]:
        writer.writerow([item["label"], item["amount"], f"{item['share']:.2f}"])
    writer.writerow([])
    writer.writerow(["Investment", "Type", "Invested", "Current", "P&L", "Return %"])
    for row in context["rows"]["stocks"]:
        writer.writerow([row["symbol"], "Stock", row["invested_value"], row["market_value"], row["pnl"], f"{row['returns_pct']:.2f}"])
    for row in context["rows"]["mutual_funds"]:
        writer.writerow([row["fund_name"], "Mutual Fund", row["invested_value"], row["current_value"], row["pnl"], f"{row['returns_pct']:.2f}"])

    payload = BytesIO(text_buffer.getvalue().encode("utf-8-sig"))
    payload.seek(0)
    return payload


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
        if column.get("read_only"):
            continue
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
    execute=execute,
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
    date_tag = datetime.utcnow().strftime("%Y-%m-%d")
    return send_file(
        workbook,
        as_attachment=True,
        download_name=f"financial_dashboard_template_{date_tag}.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@app.post("/update-workbook")
def update_workbook():
    workbook = build_workbook_from_db()
    WORKBOOK_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(WORKBOOK_PATH, "wb") as handle:
        handle.write(workbook.getvalue())
    flash("Excel workbook updated from the dashboard.", "success")
    return redirect(url_for("dashboard"))


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


@app.post("/stocks/zerodha/sync-jpm")
def zerodha_sync_jpm():
    user = get_current_user()
    if user is None:
        flash("Please log in before syncing JPM.", "error")
        return redirect(url_for("login"))

    price_data = _fetch_jpm_inr_price()
    if price_data is None:
        flash("Could not fetch JPM INR pricing from Yahoo Finance. Try again later.", "error")
        return redirect(url_for("stocks_page"))

    price_inr, usd_inr_rate = price_data
    updated_rows = _update_jpm_stock(price_inr, usd_inr_rate)
    if updated_rows == 0:
        flash("No JPM rows found in the dashboard to update.", "error")
    else:
        flash(f"Updated {updated_rows} JPM row(s) with the latest INR price.", "success")
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
    report = build_reports_context()
    return render_template("dashboard.html", metrics=report["metrics"], report=report)


@app.get("/reports")
def reports():
    return redirect(url_for("dashboard"))


@app.get("/reports/export.csv")
def reports_export_csv():
    report = build_reports_csv(build_reports_context())
    date_tag = datetime.now().strftime("%Y-%m-%d")
    return send_file(
        report,
        as_attachment=True,
        download_name=f"financial_report_{date_tag}.csv",
        mimetype="text/csv",
    )


@app.post("/reload")
def reload_data():
    workbook_file = request.files.get("workbook")
    if workbook_file and workbook_file.filename:
        suffix = Path(workbook_file.filename).suffix.lower()
        if suffix not in {".xlsx", ".xls"}:
            flash("Please upload a .xlsx or .xls file.", "error")
            return redirect(url_for("dashboard"))

        WORKBOOK_PATH.parent.mkdir(parents=True, exist_ok=True)
        try:
            workbook_file.save(WORKBOOK_PATH)
        except Exception:
            flash("Unable to save the uploaded workbook.", "error")
            return redirect(url_for("dashboard"))
    elif not WORKBOOK_PATH.exists():
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
        if entity_key == "fixed_deposits":
            query = """
            SELECT
                fd.*,
                u.full_name AS account_holder,
                b.name AS bank_name
            FROM fixed_deposits fd
            LEFT JOIN bank_accounts ba ON ba.id = fd.account_id
            LEFT JOIN users u ON u.id = ba.user_id
            LEFT JOIN banks b ON b.id = ba.bank_id
            """
        else:
            query = f"SELECT * FROM {entity['table']}"
        params = ()
        filters = []
        if search:
            for column in columns:
                if column["type"] == "text":
                    filters.append(f"{column['name']} LIKE ?")
                    params += (f"%{search}%",)
        if filters:
            query += " WHERE " + " OR ".join(filters)
        query += " ORDER BY id DESC"
        rows = fetch_all(query, params)
    if entity_key == "stocks":
        for row in rows:
            row["returns_pct"] = compute_stock_returns_pct(row)
    elif entity_key == "mutual_funds":
        for row in rows:
            latest_nav = as_float(row.get("latest_nav"))
            units = as_float(row.get("units"))
            if row.get("current_value") is not None:
                current_value = as_float(row["current_value"])
            else:
                current_value = latest_nav * units
            row["current_value"] = current_value
            row["returns_pct"] = compute_mutual_fund_returns_pct(row)
    elif entity_key == "fixed_deposits":
        for row in rows:
            row["current_amount"] = compute_fixed_deposit_current_amount(row, as_float)
            row["days_to_mature"] = compute_fixed_deposit_days_to_mature(row)
    elif entity_key == "fixed_deposits":
        for row in rows:
            row["days_to_mature"] = compute_fixed_deposit_days_to_mature(row)
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
        if entity_key == "mutual_funds":
            values.pop("current_value", None)
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
            if entity_key == "mutual_funds":
                values.pop("current_value", None)
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
