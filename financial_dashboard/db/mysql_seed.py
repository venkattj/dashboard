from __future__ import annotations

from pathlib import Path
import re
import sys
import zipfile
from typing import Any
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET

import pymysql

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class Config:
    MYSQL_HOST = "localhost"
    MYSQL_USER = "root"
    MYSQL_PASSWORD = "teja@4795"
    MYSQL_DB = "teja"


WORKBOOK_PATH = Path(r"C:\Users\venka\Desktop\Income\income\Income.xlsx")
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
        "`id` INT PRIMARY KEY AUTO_INCREMENT",
        "`full_name` VARCHAR(255) NOT NULL UNIQUE",
        "`username` VARCHAR(255) NULL UNIQUE",
        "`email` VARCHAR(255) NULL UNIQUE",
        "`password_hash` VARCHAR(255) NULL",
        "`zerodha_api_key` VARCHAR(255) NULL",
        "`zerodha_api_secret` VARCHAR(255) NULL",
        "`zerodha_access_token` VARCHAR(255) NULL",
        "`zerodha_public_token` VARCHAR(255) NULL",
        "`zerodha_user_id` VARCHAR(255) NULL",
        "`zerodha_user_name` VARCHAR(255) NULL",
        "`zerodha_token_expires_at` DATETIME NULL",
        "`zerodha_connected_at` DATETIME NULL",
        "`zerodha_last_sync_at` DATETIME NULL",
        "`created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP",
    ],
    "banks": [
        "`id` INT PRIMARY KEY AUTO_INCREMENT",
        "`name` VARCHAR(255) NOT NULL UNIQUE",
        "`created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP",
    ],
    "bank_accounts": [
        "`id` INT PRIMARY KEY AUTO_INCREMENT",
        "`user_id` INT NULL",
        "`bank_id` INT NULL",
        "`balance` DOUBLE NOT NULL DEFAULT 0",
        "`purpose` VARCHAR(255) NULL",
    ],
    "fixed_deposits": [
        "`id` INT PRIMARY KEY AUTO_INCREMENT",
        "`account_id` INT NULL",
        "`invested` DOUBLE NOT NULL DEFAULT 0",
        "`interest_rate` DOUBLE NOT NULL DEFAULT 0",
        "`maturity_date` DATE NULL",
        "`created_date` DATE NULL",
        "`current_amount` DOUBLE NOT NULL DEFAULT 0",
        "`days_to_mature` INT NULL",
    ],
    "stocks": [
        "`id` INT PRIMARY KEY AUTO_INCREMENT",
        "`symbol` VARCHAR(255) NOT NULL",
        "`exchange` VARCHAR(32) NULL",
        "`isin` VARCHAR(32) NULL",
        "`average_price` DOUBLE NOT NULL DEFAULT 0",
        "`current_price` DOUBLE NOT NULL DEFAULT 0",
        "`quantity` DOUBLE NOT NULL DEFAULT 0",
        "`source` VARCHAR(32) NOT NULL DEFAULT 'manual'",
        "`last_synced_price_at` DATETIME NULL",
    ],
    "mutual_funds": [
        "`id` INT PRIMARY KEY AUTO_INCREMENT",
        "`fund_name` VARCHAR(255) NOT NULL",
        "`scheme_code` VARCHAR(64) NULL",
        "`sip` DOUBLE NOT NULL DEFAULT 0",
        "`units` DOUBLE NOT NULL DEFAULT 0",
        "`average_nav` DOUBLE NOT NULL DEFAULT 0",
        "`latest_nav` DOUBLE NOT NULL DEFAULT 0",
        "`nav_synced_at` DATETIME NULL",
    ],
    "utility_bills": [
        "`id` INT PRIMARY KEY AUTO_INCREMENT",
        "`bill_type` VARCHAR(255) NOT NULL",
        "`amount` DOUBLE NOT NULL DEFAULT 0",
    ],
    "loans": [
        "`id` INT PRIMARY KEY AUTO_INCREMENT",
        "`borrower` VARCHAR(255) NOT NULL",
        "`amount` DOUBLE NOT NULL DEFAULT 0",
        "`interest_rate` DOUBLE NOT NULL DEFAULT 0",
    ],
    "earnings": [
        "`id` INT PRIMARY KEY AUTO_INCREMENT",
        "`income_type` VARCHAR(255) NOT NULL",
        "`amount` DOUBLE NOT NULL DEFAULT 0",
        "`person` VARCHAR(255) NOT NULL",
        "`source` VARCHAR(255) NULL",
    ],
    "spending": [
        "`id` INT PRIMARY KEY AUTO_INCREMENT",
        "`spending_type` VARCHAR(255) NOT NULL",
        "`amount` DOUBLE NOT NULL DEFAULT 0",
        "`person` VARCHAR(255) NOT NULL",
        "`recipient` VARCHAR(255) NULL",
    ],
    "standard_chits": [
        "`id` INT PRIMARY KEY AUTO_INCREMENT",
        "`organization` VARCHAR(255) NOT NULL",
        "`value` DOUBLE NOT NULL DEFAULT 0",
        "`duration_months` INT NULL",
        "`paid_months` INT NULL",
        "`emi` DOUBLE NOT NULL DEFAULT 0",
        "`maturity_date` DATE NULL",
        "`started_date` DATE NULL",
        "`current_value` DOUBLE NOT NULL DEFAULT 0",
        "`note` VARCHAR(255) NULL",
    ],
    "variable_chits": [
        "`id` INT PRIMARY KEY AUTO_INCREMENT",
        "`name` VARCHAR(255) NOT NULL",
        "`value` DOUBLE NOT NULL DEFAULT 0",
        "`months` INT NULL",
        "`maturity_date` DATE NULL",
        "`total_paid` DOUBLE NOT NULL DEFAULT 0",
        "`start_date` DATE NULL",
        "`net_value` DOUBLE NOT NULL DEFAULT 0",
        "`emi_paid` INT NULL",
    ],
    "variable_chit_payments": [
        "`id` INT PRIMARY KEY AUTO_INCREMENT",
        "`emi_no` INT NULL",
        "`amount` DOUBLE NOT NULL DEFAULT 0",
        "`payment_date` DATE NULL",
        "`actual_paid` DOUBLE NULL",
        "`start_date` DATE NULL",
    ],
    "sneha_payments": [
        "`id` INT PRIMARY KEY AUTO_INCREMENT",
        "`payment_date` DATE NULL",
        "`amount` DOUBLE NOT NULL DEFAULT 0",
        "`principal_balance` DOUBLE NULL",
    ],
    "overall_assets": [
        "`id` INT PRIMARY KEY AUTO_INCREMENT",
        "`label` VARCHAR(255) NOT NULL",
        "`amount` DOUBLE NOT NULL DEFAULT 0",
        "`note` VARCHAR(255) NULL",
    ],
}


def is_number(value: Any) -> bool:
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False


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
                    "current_amount": as_float(row[7]),
                    "days_to_mature": as_int(row[8]),
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

    for row in sheets.get("Earnings", [])[1:]:
        if len(row) >= 5 and is_number(row[0]):
            dataset["earnings"].append(
                {
                    "income_type": row[1],
                    "amount": as_float(row[2]),
                    "person": row[3],
                    "source": row[4],
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


def get_connection(database: str | None = None):
    return pymysql.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=database,
        charset="utf8mb4",
        autocommit=True,
    )


def normalize_value(value: Any) -> Any:
    if value == "":
        return None
    return value


def create_database() -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{Config.MYSQL_DB}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )


def create_tables() -> None:
    with get_connection(Config.MYSQL_DB) as conn:
        with conn.cursor() as cur:
            for table_name, columns in TABLE_DEFINITIONS.items():
                ddl = f"CREATE TABLE IF NOT EXISTS `{table_name}` ({', '.join(columns)}) ENGINE=InnoDB"
                cur.execute(ddl)
            ensure_user_auth_columns(cur)
            ensure_bank_account_reference_columns(cur)
            ensure_fixed_deposit_reference_columns(cur)
            ensure_stock_sync_columns(cur)
            ensure_mutual_fund_columns(cur)
            sync_bank_account_reference_data(cur)


def _column_exists(cur, table_name: str, column_name: str) -> bool:
    cur.execute(
        """
        SELECT 1
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s AND COLUMN_NAME = %s
        """,
        (Config.MYSQL_DB, table_name, column_name),
    )
    return cur.fetchone() is not None


def _constraint_exists(cur, table_name: str, constraint_name: str) -> bool:
    cur.execute(
        """
        SELECT 1
        FROM information_schema.TABLE_CONSTRAINTS
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s AND CONSTRAINT_NAME = %s
        """,
        (Config.MYSQL_DB, table_name, constraint_name),
    )
    return cur.fetchone() is not None


def _index_exists(cur, table_name: str, index_name: str) -> bool:
    cur.execute(
        """
        SELECT 1
        FROM information_schema.STATISTICS
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s AND INDEX_NAME = %s
        """,
        (Config.MYSQL_DB, table_name, index_name),
    )
    return cur.fetchone() is not None


def ensure_user_auth_columns(cur) -> None:
    if not _column_exists(cur, "users", "username"):
        cur.execute("ALTER TABLE `users` ADD COLUMN `username` VARCHAR(255) NULL AFTER `full_name`")
    if not _column_exists(cur, "users", "email"):
        cur.execute("ALTER TABLE `users` ADD COLUMN `email` VARCHAR(255) NULL AFTER `username`")
    if not _column_exists(cur, "users", "password_hash"):
        cur.execute("ALTER TABLE `users` ADD COLUMN `password_hash` VARCHAR(255) NULL AFTER `email`")
    if not _column_exists(cur, "users", "zerodha_api_key"):
        cur.execute("ALTER TABLE `users` ADD COLUMN `zerodha_api_key` VARCHAR(255) NULL AFTER `password_hash`")
    if not _column_exists(cur, "users", "zerodha_api_secret"):
        cur.execute("ALTER TABLE `users` ADD COLUMN `zerodha_api_secret` VARCHAR(255) NULL AFTER `zerodha_api_key`")
    if not _column_exists(cur, "users", "zerodha_access_token"):
        cur.execute("ALTER TABLE `users` ADD COLUMN `zerodha_access_token` VARCHAR(255) NULL AFTER `zerodha_api_secret`")
    if not _column_exists(cur, "users", "zerodha_public_token"):
        cur.execute("ALTER TABLE `users` ADD COLUMN `zerodha_public_token` VARCHAR(255) NULL AFTER `zerodha_access_token`")
    if not _column_exists(cur, "users", "zerodha_user_id"):
        cur.execute("ALTER TABLE `users` ADD COLUMN `zerodha_user_id` VARCHAR(255) NULL AFTER `zerodha_public_token`")
    if not _column_exists(cur, "users", "zerodha_user_name"):
        cur.execute("ALTER TABLE `users` ADD COLUMN `zerodha_user_name` VARCHAR(255) NULL AFTER `zerodha_user_id`")
    if not _column_exists(cur, "users", "zerodha_token_expires_at"):
        cur.execute("ALTER TABLE `users` ADD COLUMN `zerodha_token_expires_at` DATETIME NULL AFTER `zerodha_user_name`")
    if not _column_exists(cur, "users", "zerodha_connected_at"):
        cur.execute("ALTER TABLE `users` ADD COLUMN `zerodha_connected_at` DATETIME NULL AFTER `zerodha_token_expires_at`")
    if not _column_exists(cur, "users", "zerodha_last_sync_at"):
        cur.execute("ALTER TABLE `users` ADD COLUMN `zerodha_last_sync_at` DATETIME NULL AFTER `zerodha_connected_at`")

    if not _index_exists(cur, "users", "username"):
        cur.execute("ALTER TABLE `users` ADD UNIQUE INDEX `username` (`username`)")
    if not _index_exists(cur, "users", "email"):
        cur.execute("ALTER TABLE `users` ADD UNIQUE INDEX `email` (`email`)")


def ensure_bank_account_reference_columns(cur) -> None:
    if not _column_exists(cur, "bank_accounts", "user_id"):
        cur.execute("ALTER TABLE `bank_accounts` ADD COLUMN `user_id` INT NULL AFTER `id`")
    if not _column_exists(cur, "bank_accounts", "bank_id"):
        cur.execute("ALTER TABLE `bank_accounts` ADD COLUMN `bank_id` INT NULL AFTER `user_id`")

    if not _index_exists(cur, "bank_accounts", "idx_bank_accounts_user_id"):
        cur.execute("ALTER TABLE `bank_accounts` ADD INDEX `idx_bank_accounts_user_id` (`user_id`)")
    if not _index_exists(cur, "bank_accounts", "idx_bank_accounts_bank_id"):
        cur.execute("ALTER TABLE `bank_accounts` ADD INDEX `idx_bank_accounts_bank_id` (`bank_id`)")

    if not _constraint_exists(cur, "bank_accounts", "fk_bank_accounts_user"):
        cur.execute(
            """
            ALTER TABLE `bank_accounts`
            ADD CONSTRAINT `fk_bank_accounts_user`
            FOREIGN KEY (`user_id`) REFERENCES `users`(`id`)
            ON UPDATE CASCADE ON DELETE SET NULL
            """
        )
    if not _constraint_exists(cur, "bank_accounts", "fk_bank_accounts_bank"):
        cur.execute(
            """
            ALTER TABLE `bank_accounts`
            ADD CONSTRAINT `fk_bank_accounts_bank`
            FOREIGN KEY (`bank_id`) REFERENCES `banks`(`id`)
            ON UPDATE CASCADE ON DELETE SET NULL
            """
        )

    sync_bank_account_reference_data(cur)

    if _column_exists(cur, "bank_accounts", "account_holder"):
        cur.execute("ALTER TABLE `bank_accounts` DROP COLUMN `account_holder`")
    if _column_exists(cur, "bank_accounts", "bank_name"):
        cur.execute("ALTER TABLE `bank_accounts` DROP COLUMN `bank_name`")


def ensure_stock_sync_columns(cur) -> None:
    if not _column_exists(cur, "stocks", "exchange"):
        cur.execute("ALTER TABLE `stocks` ADD COLUMN `exchange` VARCHAR(32) NULL AFTER `symbol`")
    if not _column_exists(cur, "stocks", "isin"):
        cur.execute("ALTER TABLE `stocks` ADD COLUMN `isin` VARCHAR(32) NULL AFTER `exchange`")
    if not _column_exists(cur, "stocks", "source"):
        cur.execute("ALTER TABLE `stocks` ADD COLUMN `source` VARCHAR(32) NOT NULL DEFAULT 'manual' AFTER `quantity`")
    if not _column_exists(cur, "stocks", "last_synced_price_at"):
        cur.execute("ALTER TABLE `stocks` ADD COLUMN `last_synced_price_at` DATETIME NULL AFTER `source`")


def ensure_mutual_fund_columns(cur) -> None:
    if not _column_exists(cur, "mutual_funds", "scheme_code"):
        cur.execute("ALTER TABLE `mutual_funds` ADD COLUMN `scheme_code` VARCHAR(64) NULL AFTER `fund_name`")
    if not _column_exists(cur, "mutual_funds", "units"):
        cur.execute("ALTER TABLE `mutual_funds` ADD COLUMN `units` DOUBLE NOT NULL DEFAULT 0 AFTER `sip`")
    if not _column_exists(cur, "mutual_funds", "average_nav"):
        cur.execute("ALTER TABLE `mutual_funds` ADD COLUMN `average_nav` DOUBLE NOT NULL DEFAULT 0 AFTER `units`")
    if not _column_exists(cur, "mutual_funds", "latest_nav"):
        cur.execute("ALTER TABLE `mutual_funds` ADD COLUMN `latest_nav` DOUBLE NOT NULL DEFAULT 0 AFTER `average_nav`")
    if not _column_exists(cur, "mutual_funds", "nav_synced_at"):
        cur.execute("ALTER TABLE `mutual_funds` ADD COLUMN `nav_synced_at` DATETIME NULL AFTER `latest_nav`")

    if _column_exists(cur, "mutual_funds", "invested"):
        cur.execute("ALTER TABLE `mutual_funds` DROP COLUMN `invested`")
    if _column_exists(cur, "mutual_funds", "returns_pct"):
        cur.execute("ALTER TABLE `mutual_funds` DROP COLUMN `returns_pct`")
    if _column_exists(cur, "mutual_funds", "current_value"):
        cur.execute("ALTER TABLE `mutual_funds` DROP COLUMN `current_value`")


def ensure_fixed_deposit_reference_columns(cur) -> None:
    if not _column_exists(cur, "fixed_deposits", "account_id"):
        cur.execute("ALTER TABLE `fixed_deposits` ADD COLUMN `account_id` INT NULL AFTER `id`")

    if not _index_exists(cur, "fixed_deposits", "idx_fixed_deposits_account_id"):
        cur.execute("ALTER TABLE `fixed_deposits` ADD INDEX `idx_fixed_deposits_account_id` (`account_id`)")

    if not _constraint_exists(cur, "fixed_deposits", "fk_fixed_deposits_account"):
        cur.execute(
            """
            ALTER TABLE `fixed_deposits`
            ADD CONSTRAINT `fk_fixed_deposits_account`
            FOREIGN KEY (`account_id`) REFERENCES `bank_accounts`(`id`)
            ON UPDATE CASCADE ON DELETE SET NULL
            """
        )

    if _column_exists(cur, "fixed_deposits", "bank"):
        cur.execute("ALTER TABLE `fixed_deposits` DROP COLUMN `bank`")


def sync_bank_account_reference_data(cur) -> None:
    if _column_exists(cur, "bank_accounts", "account_holder"):
        cur.execute(
            """
            INSERT INTO `users` (`full_name`)
            SELECT DISTINCT TRIM(`account_holder`)
            FROM `bank_accounts`
            WHERE TRIM(COALESCE(`account_holder`, '')) <> ''
            ON DUPLICATE KEY UPDATE `full_name` = VALUES(`full_name`)
            """
        )
    if _column_exists(cur, "bank_accounts", "bank_name"):
        cur.execute(
            """
            INSERT INTO `banks` (`name`)
            SELECT DISTINCT TRIM(`bank_name`)
            FROM `bank_accounts`
            WHERE TRIM(COALESCE(`bank_name`, '')) <> ''
            ON DUPLICATE KEY UPDATE `name` = VALUES(`name`)
            """
        )
    if _column_exists(cur, "bank_accounts", "account_holder") and _column_exists(cur, "bank_accounts", "bank_name"):
        cur.execute(
            """
            UPDATE `bank_accounts` ba
            LEFT JOIN `users` u ON u.`full_name` = TRIM(ba.`account_holder`)
            LEFT JOIN `banks` b ON b.`name` = TRIM(ba.`bank_name`)
            SET
                ba.`user_id` = COALESCE(ba.`user_id`, u.`id`),
                ba.`bank_id` = COALESCE(ba.`bank_id`, b.`id`)
            """
        )


def truncate_tables() -> None:
    with get_connection(Config.MYSQL_DB) as conn:
        with conn.cursor() as cur:
            cur.execute("SET FOREIGN_KEY_CHECKS = 0")
            for table_name in TABLE_DEFINITIONS:
                cur.execute(f"TRUNCATE TABLE `{table_name}`")
            cur.execute("SET FOREIGN_KEY_CHECKS = 1")


def seed_tables(workbook_path: Path) -> dict[str, int]:
    dataset = parse_workbook_rows(workbook_path)
    inserted_counts: dict[str, int] = {}

    with get_connection(Config.MYSQL_DB) as conn:
        with conn.cursor() as cur:
            for table_name, rows in dataset.items():
                if not rows:
                    inserted_counts[table_name] = 0
                    continue
                columns = list(rows[0].keys())
                placeholders = ", ".join(["%s"] * len(columns))
                sql = (
                    f"INSERT INTO `{table_name}` ({', '.join(f'`{column}`' for column in columns)}) "
                    f"VALUES ({placeholders})"
                )
                payload = [
                    tuple(normalize_value(row[column]) for column in columns)
                    for row in rows
                ]
                cur.executemany(sql, payload)
                inserted_counts[table_name] = len(payload)
            sync_bank_account_reference_data(cur)

    return inserted_counts


def main() -> None:
    if not WORKBOOK_PATH.exists():
        raise FileNotFoundError(f"Workbook not found: {WORKBOOK_PATH}")

    create_database()
    create_tables()
    truncate_tables()
    counts = seed_tables(WORKBOOK_PATH)

    print(f"Schema ready: {Config.MYSQL_DB}")
    for table_name in ENTITY_ORDER:
        print(f"{table_name}: {counts.get(table_name, 0)} rows")


if __name__ == "__main__":
    main()
