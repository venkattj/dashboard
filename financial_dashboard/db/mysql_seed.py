from __future__ import annotations

from pathlib import Path
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
    "bank_accounts": [
        "`id` INT PRIMARY KEY AUTO_INCREMENT",
        "`account_holder` VARCHAR(255) NOT NULL",
        "`bank_name` VARCHAR(255) NOT NULL",
        "`balance` DOUBLE NOT NULL DEFAULT 0",
        "`purpose` VARCHAR(255) NULL",
    ],
    "fixed_deposits": [
        "`id` INT PRIMARY KEY AUTO_INCREMENT",
        "`bank` VARCHAR(255) NOT NULL",
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
        "`average_price` DOUBLE NOT NULL DEFAULT 0",
        "`current_price` DOUBLE NOT NULL DEFAULT 0",
        "`quantity` DOUBLE NOT NULL DEFAULT 0",
    ],
    "mutual_funds": [
        "`id` INT PRIMARY KEY AUTO_INCREMENT",
        "`fund_name` VARCHAR(255) NOT NULL",
        "`invested` DOUBLE NOT NULL DEFAULT 0",
        "`returns_pct` DOUBLE NOT NULL DEFAULT 0",
        "`sip` DOUBLE NOT NULL DEFAULT 0",
        "`current_value` DOUBLE NOT NULL DEFAULT 0",
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

    for row in sheets.get("Bank", [])[1:]:
        if len(row) >= 5 and is_number(row[0]):
            dataset["bank_accounts"].append(
                {
                    "account_holder": row[1],
                    "bank_name": row[2],
                    "balance": as_float(row[3]),
                    "purpose": row[4],
                }
            )

    for row in sheets.get("Fixed Deposit", [])[1:]:
        if len(row) >= 9 and is_number(row[0]):
            dataset["fixed_deposits"].append(
                {
                    "bank": row[1],
                    "invested": as_float(row[2]),
                    "interest_rate": as_float(row[3]),
                    "maturity_date": row[4],
                    "created_date": row[5],
                    "current_amount": as_float(row[7]),
                    "days_to_mature": as_int(row[8]),
                }
            )

    for row in sheets.get("Stocks", [])[1:]:
        if len(row) >= 5 and row[1] and row[1] != "Summary":
            if is_number(row[2]) and is_number(row[3]) and is_number(row[4]):
                dataset["stocks"].append(
                    {
                        "symbol": row[1],
                        "average_price": as_float(row[2]),
                        "current_price": as_float(row[3]),
                        "quantity": as_float(row[4]),
                    }
                )

    for row in sheets.get("Mutal Funds", [])[1:]:
        if len(row) < 6:
            continue
        fund_name = str(row[1]).strip() if len(row) > 1 and row[1] is not None else ""
        if not fund_name or is_number(fund_name):
            continue
        if not (is_number(row[2]) and is_number(row[3]) and is_number(row[4]) and is_number(row[5])):
            continue
        dataset["mutual_funds"].append(
            {
                "fund_name": fund_name,
                "invested": as_float(row[2]),
                "returns_pct": as_float(row[3]),
                "sip": as_float(row[4]),
                "current_value": as_float(row[5]),
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
