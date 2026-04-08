from __future__ import annotations

from pathlib import Path
import re
import sqlite3
import sys
import zipfile
from typing import Any
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


WORKBOOK_PATH = PROJECT_ROOT / "Income.xlsx"
NS = {
    "a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}
EXCEL_BASE_DATE = datetime(1899, 12, 30)
ENTITY_ORDER = [
    "users",
    "banks",
    "bank_accounts",
    "fixed_deposits",
    "stocks",
    "mutual_funds",
    "utility_bills",
    "loans",
    "earnings",
    "spending",
    "standard_chits",
    "variable_chits",
    "variable_chit_payments",
    "sneha_payments",
    "overall_assets",
]


TABLE_DEFINITIONS = {
    "users": [
        "id INTEGER PRIMARY KEY AUTOINCREMENT",
        "full_name TEXT NOT NULL UNIQUE",
        "username TEXT UNIQUE",
        "email TEXT UNIQUE",
        "password_hash TEXT",
        "zerodha_api_key TEXT",
        "zerodha_api_secret TEXT",
        "zerodha_access_token TEXT",
        "zerodha_public_token TEXT",
        "zerodha_user_id TEXT",
        "zerodha_user_name TEXT",
        "zerodha_token_expires_at TEXT",
        "zerodha_connected_at TEXT",
        "zerodha_last_sync_at TEXT",
        "created_at TEXT DEFAULT CURRENT_TIMESTAMP",
    ],
    "banks": [
        "id INTEGER PRIMARY KEY AUTOINCREMENT",
        "name TEXT NOT NULL UNIQUE",
        "created_at TEXT DEFAULT CURRENT_TIMESTAMP",
    ],
    "bank_accounts": [
        "id INTEGER PRIMARY KEY AUTOINCREMENT",
        "user_id INTEGER",
        "bank_id INTEGER",
        "balance REAL NOT NULL DEFAULT 0",
        "purpose TEXT",
    ],
    "fixed_deposits": [
        "id INTEGER PRIMARY KEY AUTOINCREMENT",
        "account_id INTEGER",
        "invested REAL NOT NULL DEFAULT 0",
        "interest_rate REAL NOT NULL DEFAULT 0",
        "maturity_date TEXT",
        "created_date TEXT",
    ],
    "stocks": [
        "id INTEGER PRIMARY KEY AUTOINCREMENT",
        "symbol TEXT NOT NULL",
        "exchange TEXT",
        "isin TEXT",
        "average_price REAL NOT NULL DEFAULT 0",
        "current_price REAL NOT NULL DEFAULT 0",
        "quantity REAL NOT NULL DEFAULT 0",
        "source TEXT NOT NULL DEFAULT 'manual'",
        "last_synced_price_at TEXT",
    ],
    "mutual_funds": [
        "id INTEGER PRIMARY KEY AUTOINCREMENT",
        "fund_name TEXT NOT NULL",
        "scheme_code TEXT",
        "sip REAL NOT NULL DEFAULT 0",
        "units REAL NOT NULL DEFAULT 0",
        "average_nav REAL NOT NULL DEFAULT 0",
        "latest_nav REAL NOT NULL DEFAULT 0",
        "nav_synced_at TEXT",
    ],
    "utility_bills": [
        "id INTEGER PRIMARY KEY AUTOINCREMENT",
        "bill_type TEXT NOT NULL",
        "amount REAL NOT NULL DEFAULT 0",
    ],
    "loans": [
        "id INTEGER PRIMARY KEY AUTOINCREMENT",
        "borrower TEXT NOT NULL",
        "amount REAL NOT NULL DEFAULT 0",
        "interest_rate REAL NOT NULL DEFAULT 0",
    ],
    "earnings": [
        "id INTEGER PRIMARY KEY AUTOINCREMENT",
        "income_type TEXT NOT NULL",
        "amount REAL NOT NULL DEFAULT 0",
        "person TEXT NOT NULL",
        "source TEXT",
    ],
    "spending": [
        "id INTEGER PRIMARY KEY AUTOINCREMENT",
        "spending_type TEXT NOT NULL",
        "amount REAL NOT NULL DEFAULT 0",
        "person TEXT NOT NULL",
        "recipient TEXT",
    ],
    "standard_chits": [
        "id INTEGER PRIMARY KEY AUTOINCREMENT",
        "organization TEXT NOT NULL",
        "value REAL NOT NULL DEFAULT 0",
        "duration_months INTEGER",
        "paid_months INTEGER",
        "emi REAL NOT NULL DEFAULT 0",
        "maturity_date TEXT",
        "started_date TEXT",
        "current_value REAL NOT NULL DEFAULT 0",
        "note TEXT",
    ],
    "variable_chits": [
        "id INTEGER PRIMARY KEY AUTOINCREMENT",
        "name TEXT NOT NULL",
        "value REAL NOT NULL DEFAULT 0",
        "months INTEGER",
        "maturity_date TEXT",
        "total_paid REAL NOT NULL DEFAULT 0",
        "start_date TEXT",
        "net_value REAL NOT NULL DEFAULT 0",
        "emi_paid INTEGER",
    ],
    "variable_chit_payments": [
        "id INTEGER PRIMARY KEY AUTOINCREMENT",
        "emi_no INTEGER",
        "amount REAL NOT NULL DEFAULT 0",
        "payment_date TEXT",
        "actual_paid REAL",
        "start_date TEXT",
    ],
    "sneha_payments": [
        "id INTEGER PRIMARY KEY AUTOINCREMENT",
        "payment_date TEXT",
        "amount REAL NOT NULL DEFAULT 0",
        "principal_balance REAL",
    ],
    "overall_assets": [
        "id INTEGER PRIMARY KEY AUTOINCREMENT",
        "label TEXT NOT NULL",
        "amount REAL NOT NULL DEFAULT 0",
        "note TEXT",
    ],
}


def is_number(value: Any) -> bool:
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False


def normalize_header_label(value: Any) -> str:
    text = str(value or "").lower()
    return "".join(ch for ch in text if ch.isalnum())


def find_last_matching_column(headers: list[Any], candidates: set[str]) -> int | None:
    normalized_headers = [normalize_header_label(header) for header in headers]
    normalized_candidates = {normalize_header_label(candidate) for candidate in candidates}
    for idx in range(len(headers) - 1, -1, -1):
        if normalized_headers[idx] in normalized_candidates:
            return idx
    return None


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


def maybe_excel_date(raw_value: str, style_idx: int | None, style_ids: list[int]) -> str:
    try:
        number = float(raw_value)
    except (TypeError, ValueError):
        return raw_value
    num_fmt = style_ids[style_idx] if style_idx is not None and style_idx < len(style_ids) else 0
    if num_fmt in {14, 15, 16, 17, 22, 27, 30, 36, 50, 57} and 20000 < number < 60000:
        return (EXCEL_BASE_DATE + timedelta(days=number)).strftime("%Y-%m-%d")
    return raw_value


def read_workbook(path: Path) -> dict[str, list[list[str]]]:
    with zipfile.ZipFile(path) as workbook_zip:
        shared_strings: list[str] = []
        if "xl/sharedStrings.xml" in workbook_zip.namelist():
            shared_root = ET.fromstring(workbook_zip.read("xl/sharedStrings.xml"))
            for item in shared_root.findall("a:si", NS):
                shared_strings.append("".join(node.text or "" for node in item.iterfind(".//a:t", NS)))

        style_ids: list[int] = []
        if "xl/styles.xml" in workbook_zip.namelist():
            styles_root = ET.fromstring(workbook_zip.read("xl/styles.xml"))
            cell_xfs = styles_root.find("a:cellXfs", NS)
            if cell_xfs is not None:
                for xf in cell_xfs.findall("a:xf", NS):
                    style_ids.append(int(xf.attrib.get("numFmtId", "0")))

        def cell_value(cell: ET.Element) -> str:
            cell_type = cell.attrib.get("t")
            style_idx = int(cell.attrib["s"]) if "s" in cell.attrib else None
            if cell_type == "inlineStr":
                return "".join(node.text or "" for node in cell.iterfind(".//a:t", NS))
            value_node = cell.find("a:v", NS)
            if value_node is None:
                return ""
            if cell_type == "s":
                return shared_strings[int(value_node.text)]
            return maybe_excel_date(value_node.text or "", style_idx, style_ids)

        workbook_root = ET.fromstring(workbook_zip.read("xl/workbook.xml"))
        rel_root = ET.fromstring(workbook_zip.read("xl/_rels/workbook.xml.rels"))
        rel_map = {rel.attrib["Id"]: rel.attrib["Target"] for rel in rel_root}

        parsed: dict[str, list[list[str]]] = {}
        for sheet in workbook_root.find("a:sheets", NS):
            sheet_name = sheet.attrib["name"]
            relationship_id = sheet.attrib["{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"]
            sheet_root = ET.fromstring(workbook_zip.read("xl/" + rel_map[relationship_id]))
            rows = sheet_root.find("a:sheetData", NS)
            parsed[sheet_name] = []
            if rows is None:
                continue
            for row in rows.findall("a:row", NS):
                parsed[sheet_name].append([cell_value(cell) for cell in row.findall("a:c", NS)])
        return parsed


def parse_workbook_rows(path: Path) -> dict[str, list[dict[str, Any]]]:
    sheets = read_workbook(path)
    dataset = {name: [] for name in TABLE_DEFINITIONS}
    user_name_by_sheet_id: dict[int, str] = {}
    bank_name_by_sheet_id: dict[int, str] = {}

    user_rows = sheets.get("Users", [])
    if user_rows:
        headers = [str(value).strip() for value in user_rows[0]]
        supported_user_columns = {
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
        }
        for row in user_rows[1:]:
            if not row or not any(str(cell).strip() for cell in row):
                continue
            values = {headers[idx]: row[idx] if idx < len(row) else "" for idx in range(len(headers))}
            full_name = str(values.get("full_name", "")).strip()
            if not full_name:
                continue
            raw_id = str(values.get("id", "")).strip()
            if raw_id.isdigit():
                user_name_by_sheet_id[int(raw_id)] = full_name
            dataset["users"].append(
                {
                    column: values.get(column, "")
                    for column in headers
                    if column in supported_user_columns
                }
            )

    bank_master_rows = sheets.get("Banks", [])
    if bank_master_rows:
        headers = [str(value).strip() for value in bank_master_rows[0]]
        for row in bank_master_rows[1:]:
            if not row or not any(str(cell).strip() for cell in row):
                continue
            values = {headers[idx]: row[idx] if idx < len(row) else "" for idx in range(len(headers))}
            bank_name = str(values.get("name", "")).strip()
            if not bank_name:
                continue
            raw_id = str(values.get("id", "")).strip()
            if raw_id.isdigit():
                bank_name_by_sheet_id[int(raw_id)] = bank_name
            dataset["banks"].append({"name": bank_name})

    bank_account_rows = sheets.get("bank_accounts", [])
    if bank_account_rows:
        headers = [str(value).strip() for value in bank_account_rows[0]]
        for row in bank_account_rows[1:]:
            if not row or not any(str(cell).strip() for cell in row):
                continue
            values = {headers[idx]: row[idx] if idx < len(row) else "" for idx in range(len(headers))}
            raw_user_id = str(values.get("user_id", "")).strip()
            raw_bank_id = str(values.get("bank_id", "")).strip()
            balance = values.get("balance", "")
            if not raw_user_id or not raw_bank_id or not is_number(balance):
                continue
            user_id = int(raw_user_id) if raw_user_id.isdigit() else None
            bank_id = int(raw_bank_id) if raw_bank_id.isdigit() else None
            account_holder = user_name_by_sheet_id.get(user_id or 0, "")
            bank_name = bank_name_by_sheet_id.get(bank_id or 0, "")
            if not account_holder or not bank_name:
                continue
            dataset["bank_accounts"].append(
                {
                    "user_id": user_id,
                    "bank_id": bank_id,
                    "balance": as_float(balance),
                    "purpose": str(values.get("purpose", "")).strip(),
                }
            )

    for row in sheets.get("Fixed Deposit", [])[1:]:
        if len(row) >= 9 and is_number(row[0]):
            dataset["fixed_deposits"].append(
                {
                    "account_id": as_int(row[1]),
                    "invested": as_float(row[2]),
                    "interest_rate": as_float(row[3]),
                    "maturity_date": row[4],
                    "created_date": row[5],
                }
            )

    for row in sheets.get("Stocks", [])[1:]:
        if len(row) >= 8 and row[1] and row[1] != "Summary":
            if is_number(row[4]) and is_number(row[5]) and is_number(row[6]):
                dataset["stocks"].append(
                    {
                        "symbol": row[1],
                        "exchange": row[2],
                        "isin": row[3],
                        "average_price": as_float(row[4]),
                        "current_price": as_float(row[5]),
                        "quantity": as_float(row[6]),
                        "source": row[7] or "manual",
                    }
                )
        elif len(row) >= 5 and row[1] and row[1] != "Summary":
            if is_number(row[2]) and is_number(row[3]) and is_number(row[4]):
                dataset["stocks"].append(
                    {
                        "symbol": row[1],
                        "average_price": as_float(row[2]),
                        "current_price": as_float(row[3]),
                        "quantity": as_float(row[4]),
                        "source": "manual",
                    }
                )

    mutual_rows = sheets.get("Mutal Funds", [])
    if len(mutual_rows) > 1:
        headers = [str(value).strip() for value in mutual_rows[0]]

        def col_index(*variants: str) -> int | None:
            normalized = {re.sub(r'[^a-z0-9]', '', header.lower()): idx for idx, header in enumerate(headers)}
            for variant in variants:
                idx = normalized.get(re.sub(r'[^a-z0-9]', '', variant.lower()))
                if idx is not None:
                    return idx
            return None

        fund_idx = col_index('fund name', 'name', 'fund_name')
        scheme_idx = col_index('scheme code', 'scheme_code', 'schemecode')
        sip_idx = col_index('sip', 'monthly sip', 'monthly_sip')
        units_idx = col_index('units',)
        avg_nav_idx = col_index('average nav', 'average_nav', 'avg nav', 'avg_nav')
        latest_nav_idx = col_index('latest nav', 'latest_nav', 'current nav', 'current_nav')
        synced_idx = col_index('nav synced at', 'nav_synced_at', 'synced at')

        for row in mutual_rows[1:]:
            fund_name = (row[fund_idx] if fund_idx is not None and fund_idx < len(row) else "") if fund_idx is not None else ""
            fund_name = str(fund_name).strip()
            if not fund_name or is_number(fund_name):
                continue
            scheme_value = (
                str(row[scheme_idx]).strip() if scheme_idx is not None and scheme_idx < len(row) and row[scheme_idx] is not None else ""
            )
            sip_value = as_float(row[sip_idx]) if sip_idx is not None and sip_idx < len(row) else 0.0
            units_value = as_float(row[units_idx]) if units_idx is not None and units_idx < len(row) else 0.0
            average_nav_value = as_float(row[avg_nav_idx]) if avg_nav_idx is not None and avg_nav_idx < len(row) else 0.0
            latest_nav_value = as_float(row[latest_nav_idx]) if latest_nav_idx is not None and latest_nav_idx < len(row) else 0.0
            nav_synced_value = (
                str(row[synced_idx]).strip() if synced_idx is not None and synced_idx < len(row) and row[synced_idx] else None
            )
            dataset["mutual_funds"].append(
                {
                    "fund_name": fund_name,
                    "scheme_code": scheme_value,
                    "sip": sip_value,
                    "units": units_value,
                    "average_nav": average_nav_value,
                    "latest_nav": latest_nav_value,
                    "nav_synced_at": nav_synced_value,
                }
            )

    for row in sheets.get("Utility Bills", [])[1:]:
        if len(row) >= 3 and is_number(row[0]):
            dataset["utility_bills"].append({"bill_type": row[1], "amount": as_float(row[2])})

    for row in sheets.get("Loans", [])[1:]:
        if len(row) >= 4 and is_number(row[0]):
            dataset["loans"].append(
                {"borrower": row[1], "amount": as_float(row[2]), "interest_rate": as_float(row[3])}
            )

    earnings_rows = sheets.get("Earnings", [])
    if earnings_rows:
        headers = earnings_rows[0]
        income_type_index = find_last_matching_column(headers, {"income type", "type"})
        amount_index = find_last_matching_column(headers, {"amount"})
        person_index = find_last_matching_column(headers, {"person"})
        source_index = find_last_matching_column(headers, {"source", "from"})

        if amount_index is None and len(headers) > 2:
            amount_index = 2
        if income_type_index is None and len(headers) > 1:
            income_type_index = 1
        if person_index is None and len(headers) > 3:
            person_index = 3
        if source_index is None and len(headers) > 4:
            source_index = 4

        for row in earnings_rows[1:]:
            income_type = (
                str(row[income_type_index]).strip()
                if income_type_index is not None and income_type_index < len(row)
                else ""
            )
            amount_cell = (
                row[amount_index] if amount_index is not None and amount_index < len(row) else ""
            )
            if not income_type or not is_number(amount_cell):
                continue
            dataset["earnings"].append(
                {
                    "income_type": income_type,
                    "amount": as_float(amount_cell),
                    "person": row[person_index] if person_index is not None and person_index < len(row) else "",
                    "source": row[source_index] if source_index is not None and source_index < len(row) else "",
                }
            )

    for row in sheets.get("Spending", [])[1:]:
        if len(row) >= 4 and row[0] != "Total":
            dataset["spending"].append(
                {
                    "spending_type": row[0],
                    "amount": as_float(row[1]),
                    "person": row[2],
                    "recipient": row[3],
                }
            )

    for row in sheets.get("Standard_Chits", [])[1:]:
        if len(row) >= 9 and is_number(row[0]):
            dataset["standard_chits"].append(
                {
                    "organization": row[1],
                    "value": as_float(row[2]),
                    "duration_months": as_int(row[3]),
                    "paid_months": as_int(row[4]),
                    "emi": as_float(row[5]),
                    "maturity_date": row[6],
                    "started_date": row[7],
                    "current_value": as_float(row[8]),
                    "note": row[9] if len(row) > 9 else "",
                }
            )

    variable_rows = sheets.get("Variable_Chit", [])
    if len(variable_rows) > 1:
        summary = variable_rows[1]
        if len(summary) >= 8:
            dataset["variable_chits"].append(
                {
                    "name": summary[0],
                    "value": as_float(summary[1]),
                    "months": as_int(summary[2]),
                    "maturity_date": summary[3],
                    "total_paid": as_float(summary[4]),
                    "start_date": summary[5],
                    "net_value": as_float(summary[6]),
                    "emi_paid": as_int(summary[7]),
                }
            )
    for row in variable_rows[3:]:
        if len(row) >= 3 and is_number(row[0]):
            dataset["variable_chit_payments"].append(
                {
                    "emi_no": as_int(row[0]),
                    "amount": as_float(row[1]),
                    "payment_date": row[2],
                    "actual_paid": as_float(row[3]) if len(row) > 3 and row[3] else None,
                    "start_date": row[4] if len(row) > 4 else "",
                }
            )

    for row in sheets.get("sneha", [])[1:]:
        if len(row) >= 3 and is_number(row[0]):
            dataset["sneha_payments"].append(
                {
                    "payment_date": row[1],
                    "amount": as_float(row[2]),
                    "principal_balance": as_float(row[3]) if len(row) > 3 and row[3] else None,
                }
            )

    for row in sheets.get("Overall", []):
        if len(row) >= 2 and row[0] and is_number(row[1]) and row[0].lower() != "total":
            note = " | ".join(part for part in row[2:] if part)
            dataset["overall_assets"].append({"label": row[0], "amount": as_float(row[1]), "note": note})

    return dataset


SQLITE_CONNECTION: sqlite3.Connection | None = None


def _ensure_connection() -> sqlite3.Connection:
    global SQLITE_CONNECTION
    if SQLITE_CONNECTION is None:
        SQLITE_CONNECTION = sqlite3.connect(":memory:", check_same_thread=False)
        SQLITE_CONNECTION.row_factory = sqlite3.Row
    return SQLITE_CONNECTION


class CursorProxy:
    def __init__(self, cursor: sqlite3.Cursor, connection: sqlite3.Connection):
        self.cursor = cursor
        self.connection = connection

    def __enter__(self) -> sqlite3.Cursor:
        return self.cursor

    def __exit__(self, exc_type, exc, exc_tb):
        if exc_type is None:
            self.connection.commit()
        self.cursor.close()


class ConnectionProxy:
    def __init__(self, connection: sqlite3.Connection):
        self._connection = connection

    def __enter__(self) -> "ConnectionProxy":
        return self

    def __exit__(self, exc_type, exc, exc_tb):
        return False

    def cursor(self) -> CursorProxy:
        return CursorProxy(self._connection.cursor(), self._connection)

    def execute(self, *args, **kwargs):
        cursor = self._connection.cursor()
        try:
            result = cursor.execute(*args, **kwargs)
            self._connection.commit()
            return result
        finally:
            cursor.close()

    def executemany(self, *args, **kwargs):
        cursor = self._connection.cursor()
        try:
            result = cursor.executemany(*args, **kwargs)
            self._connection.commit()
            return result
        finally:
            cursor.close()

    def __getattr__(self, name):
        return getattr(self._connection, name)


def get_connection(database: str | None = None) -> ConnectionProxy:
    return ConnectionProxy(_ensure_connection())


def normalize_value(value: Any) -> Any:
    if value == "":
        return None
    return value


def create_database() -> None:
    _ensure_connection()


def create_tables() -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            for table_name, columns in TABLE_DEFINITIONS.items():
                ddl = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(columns)})"
                cur.execute(ddl)


def truncate_tables() -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            for table_name in TABLE_DEFINITIONS:
                cur.execute(f"DELETE FROM {table_name}")


def seed_tables(workbook_path: Path) -> dict[str, int]:
    dataset = parse_workbook_rows(workbook_path)
    inserted_counts: dict[str, int] = {}

    with get_connection() as conn:
        with conn.cursor() as cur:
            for table_name, rows in dataset.items():
                if not rows:
                    inserted_counts[table_name] = 0
                    continue
                columns = list(rows[0].keys())
                placeholders = ", ".join(["?"] * len(columns))
                column_names = ", ".join(columns)
                sql = f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})"
                payload = [tuple(normalize_value(row[column]) for column in columns) for row in rows]
                cur.executemany(sql, payload)
                inserted_counts[table_name] = len(payload)

    return inserted_counts


def main() -> None:
    if not WORKBOOK_PATH.exists():
        raise FileNotFoundError(f"Workbook not found: {WORKBOOK_PATH}")

    create_database()
    create_tables()
    truncate_tables()
    counts = seed_tables(WORKBOOK_PATH)

    print("Schema ready: in-memory SQLite")
    for table_name in ENTITY_ORDER:
        print(f"{table_name}: {counts.get(table_name, 0)} rows")


if __name__ == "__main__":
    main()
