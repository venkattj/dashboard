from __future__ import annotations

from datetime import date, datetime
from typing import Any, Callable

try:
    from .predictions import build_entity_prediction
except ImportError:
    from routes.predictions import build_entity_prediction


def _section(
    entity_key: str,
    entity_config: dict[str, Any],
    rows: list[dict[str, Any]],
    total: float,
    total_label: str,
    total_field: str,
    highlights: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "entity_key": entity_key,
        "entity": entity_config[entity_key],
        "rows": rows,
        "total": total,
        "total_label": total_label,
        "total_field": total_field,
        "highlights": highlights,
    }


def _with_predictions(sections: list[dict[str, Any]], as_float: Callable[[Any], float]) -> list[dict[str, Any]]:
    for section in sections:
        section["prediction"] = build_entity_prediction(
            section["entity_key"],
            section["rows"],
            as_float(section["total"]),
            as_float,
        )
    return sections


def _stock_returns_pct(row: dict[str, Any], as_float: Callable[[Any], float]) -> float:
    average = as_float(row.get("average_price"))
    current = as_float(row.get("current_price"))
    if average:
        return ((current - average) / average) * 100
    return 0.0


def _mutual_fund_invested(row: dict[str, Any], as_float: Callable[[Any], float]) -> float:
    invested_from_column = row.get("amount_invested")
    if invested_from_column is not None:
        return as_float(invested_from_column)
    return as_float(row.get("average_nav")) * as_float(row.get("units"))


def _mutual_fund_current_value(row: dict[str, Any], as_float: Callable[[Any], float]) -> float:
    return as_float(row.get("latest_nav")) * as_float(row.get("units"))


def _mutual_fund_returns_pct(row: dict[str, Any], as_float: Callable[[Any], float]) -> float:
    invested = _mutual_fund_invested(row, as_float)
    current_value_source = row.get("current_value")
    if current_value_source is not None:
        current_value = as_float(current_value_source)
    else:
        current_value = _mutual_fund_current_value(row, as_float)
    if invested:
        return ((current_value - invested) / invested) * 100
    return 0.0


def _normalize_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        text = value.strip()
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
    return None


def compute_fixed_deposit_current_amount(row: dict[str, Any], as_float: Callable[[Any], float], today: date | None = None) -> float:
    invested = as_float(row.get("invested"))
    if invested <= 0:
        return 0.0
    rate_pct = as_float(row.get("interest_rate"))
    rate = rate_pct / 100.0
    created_date = _normalize_date(row.get("created_date"))
    maturity_date = _normalize_date(row.get("maturity_date"))
    base = today or datetime.now().date()
    start = created_date or base
    end = maturity_date or base
    if end > base:
        end = base
    duration_days = max((end - start).days, 0)
    accrued = invested * rate * (duration_days / 365)
    return invested + accrued


def compute_fixed_deposit_days_to_mature(row: dict[str, Any], today: date | None = None) -> int | None:
    maturity_date = _normalize_date(row.get("maturity_date"))
    if maturity_date is None:
        return None
    base = today or datetime.now().date()
    return max((maturity_date - base).days, 0)


def build_banking_workspace(
    entity_config: dict[str, Any],
    fetch_all: Callable[..., list],
    as_float: Callable[[Any], float],
) -> dict[str, Any]:
    bank_rows = fetch_all(
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
        ORDER BY ba.balance DESC, ba.id DESC
        """
    )
    fd_rows = fetch_all(
        """
        SELECT
            fd.*,
            u.full_name AS account_holder,
            b.name AS bank_name,
            ba.purpose AS account_purpose,
            CONCAT(COALESCE(u.full_name, 'Unknown'), ' / ', COALESCE(b.name, 'Unknown')) AS account_label,
            CONCAT(COALESCE(u.full_name, 'Unknown'), ' / ', COALESCE(b.name, 'Unknown')) AS bank
        FROM fixed_deposits fd
        LEFT JOIN bank_accounts ba ON ba.id = fd.account_id
        LEFT JOIN users u ON u.id = ba.user_id
        LEFT JOIN banks b ON b.id = ba.bank_id
        ORDER BY fd.id DESC
        """
    )

    bank_total = sum(as_float(row["balance"]) for row in bank_rows)
    today = datetime.now().date()
    for row in fd_rows:
        row["current_amount"] = compute_fixed_deposit_current_amount(row, as_float, today)
        row["days_to_mature"] = compute_fixed_deposit_days_to_mature(row, today)
    fd_total = sum(as_float(row["current_amount"]) for row in fd_rows)
    fd_invested = sum(as_float(row["invested"]) for row in fd_rows)
    low_balance_count = sum(1 for row in bank_rows if as_float(row["balance"]) < 5000)
    soon_maturing = sum(
        1 for row in fd_rows if row.get("days_to_mature") is not None and 0 <= row["days_to_mature"] <= 120
    )
    maturing_30 = sum(
        1 for row in fd_rows if row.get("days_to_mature") is not None and 0 <= row["days_to_mature"] <= 30
    )
    maturing_90 = sum(
        1 for row in fd_rows if row.get("days_to_mature") is not None and 0 <= row["days_to_mature"] <= 90
    )
    maturing_30_amount = sum(
        as_float(row["current_amount"])
        for row in fd_rows
        if row.get("days_to_mature") is not None and 0 <= row["days_to_mature"] <= 30
    )
    maturing_90_amount = sum(
        as_float(row["current_amount"])
        for row in fd_rows
        if row.get("days_to_mature") is not None and 0 <= row["days_to_mature"] <= 90
    )
    top_account = max(bank_rows, key=lambda row: as_float(row["balance"]), default=None)
    top_fd = max(fd_rows, key=lambda row: as_float(row["current_amount"]), default=None)
    next_maturity = min(
        (row for row in fd_rows if row.get("days_to_mature") is not None),
        key=lambda row: row["days_to_mature"],
        default=None,
    )
    average_fd_rate = (
        sum(as_float(row["interest_rate"]) for row in fd_rows) / len(fd_rows)
        if fd_rows
        else 0
    )
    weighted_fd_rate = (
        sum(as_float(row["interest_rate"]) * as_float(row["current_amount"]) for row in fd_rows) / fd_total
        if fd_total
        else 0
    )
    average_bank_balance = (bank_total / len(bank_rows)) if bank_rows else 0
    liquidity_ratio = ((bank_total / (bank_total + fd_total)) * 100) if (bank_total + fd_total) else 0

    holder_totals: dict[str, float] = {}
    bank_totals: dict[str, float] = {}
    fd_account_totals: dict[str, float] = {}
    for row in bank_rows:
        holder = row["account_holder"] or "Unknown"
        bank = row["bank_name"] or "Unknown"
        holder_totals[holder] = holder_totals.get(holder, 0.0) + as_float(row["balance"])
        bank_totals[bank] = bank_totals.get(bank, 0.0) + as_float(row["balance"])
    for row in fd_rows:
        label = row["account_label"] or "Unknown"
        fd_account_totals[label] = fd_account_totals.get(label, 0.0) + as_float(row["current_amount"])

    top_holder_name, top_holder_total = max(holder_totals.items(), key=lambda item: item[1], default=("No data", 0.0))
    top_bank_name, top_bank_total = max(bank_totals.items(), key=lambda item: item[1], default=("No data", 0.0))
    top_fd_account_name, top_fd_account_total = max(fd_account_totals.items(), key=lambda item: item[1], default=("No data", 0.0))

    return {
        "page_title": "Banking & Deposits",
        "eyebrow": "Cash Workspace",
        "heading": "See liquid cash, maturity runway, and parked deposits from one banking command view.",
        "description": "This workspace combines operating balances with fixed deposits so you can judge liquidity, rollover pressure, and concentration by holder, bank, and linked deposit account in one place.",
        "chips": [
            {"label": f"{len(bank_rows)} bank accounts"},
            {"label": f"{len(bank_totals)} banks covered"},
            {"label": f"{len(fd_rows)} fixed deposits"},
            {"label": f"{maturing_30} FDs due in 30 days"},
        ],
        "metrics": [
            {"label": "Available Cash", "value": bank_total, "note": f"Average balance Rs. {average_bank_balance:,.2f} across {len(bank_rows)} active accounts."},
            {"label": "FD Book Value", "value": fd_total, "note": f"{len(fd_rows)} deposits currently worth Rs. {fd_total:,.2f}."},
            {"label": "Total Treasury", "value": bank_total + fd_total, "note": f"Liquidity mix is {liquidity_ratio:,.1f}% bank balance and {100 - liquidity_ratio:,.1f}% fixed deposits."},
            {"label": "Locked-In Gain", "value": fd_total - fd_invested, "note": f"Weighted FD rate is {weighted_fd_rate:,.2f}% with {maturing_90} deposits due inside 90 days."},
        ],
        "sections": _with_predictions([
            _section(
                "bank_accounts",
                entity_config,
                bank_rows,
                bank_total,
                "visible bank balance",
                "balance",
                [
                    {"label": "Top account", "value": top_account["bank_name"] if top_account else "No data", "note": f"{top_account['account_holder']} · Rs. {as_float(top_account['balance']):,.2f}" if top_account else "No balances available."},
                    {"label": "Top holder", "value": top_holder_name, "note": f"Rs. {top_holder_total:,.2f} across linked accounts."},
                    {"label": "Top bank exposure", "value": top_bank_name, "note": f"Rs. {top_bank_total:,.2f} parked with this bank."},
                    {"label": "Low balance count", "value": low_balance_count, "note": "Accounts below Rs. 5,000 and likely used mainly for routing, pension, or SIP debits."},
                ],
            ),
            _section(
                "fixed_deposits",
                entity_config,
                fd_rows,
                fd_total,
                "visible FD value",
                "current_amount",
                [
                    {
                        "label": "Next renewal FD",
                        "value": next_maturity["account_label"] if next_maturity else "No data",
                        "note": (
                            f"{next_maturity['days_to_mature']} days left · matures on {next_maturity['maturity_date']}"
                            if next_maturity and next_maturity.get("days_to_mature") is not None
                            else "No active FD maturities available."
                        ),
                    },
                    {"label": "Due in 30 days", "value": f"Rs. {maturing_30_amount:,.2f}", "note": f"{maturing_30} deposit{'s' if maturing_30 != 1 else ''} available for renewal or withdrawal."},
                    {"label": "Due in 90 days", "value": f"Rs. {maturing_90_amount:,.2f}", "note": f"{maturing_90} deposit{'s' if maturing_90 != 1 else ''} mature inside the next quarter."},
                    {"label": "Weighted rate", "value": f"{weighted_fd_rate:,.2f}%", "note": f"Locked-in gain is Rs. {fd_total - fd_invested:,.2f} across {len(fd_rows)} deposits."},
                ],
            ),
        ], as_float),
        "nav_key": "bank_accounts",
    }


def build_markets_workspace(
    entity_config: dict[str, Any],
    fetch_all: Callable[..., list],
    as_float: Callable[[Any], float],
    mutual_fund_rows: list[dict[str, Any]] | None = None,
    focus: str = "all",
) -> dict[str, Any]:
    stock_rows = fetch_all("SELECT * FROM stocks ORDER BY current_price * quantity DESC, id DESC")
    mf_rows = mutual_fund_rows if mutual_fund_rows is not None else fetch_all(
        "SELECT * FROM mutual_funds ORDER BY latest_nav * units DESC, id DESC"
    )

    enriched_mf_rows = []
    for row in mf_rows:
        current_value_source = row.get("current_value")
        if current_value_source is not None:
            current_value = as_float(current_value_source)
        else:
            current_value = _mutual_fund_current_value(row, as_float)
        returns_pct = _mutual_fund_returns_pct({**row, "current_value": current_value}, as_float)
        enriched_mf_rows.append({**row, "current_value": current_value, "returns_pct": returns_pct})

    enriched_stock_rows = []
    for row in stock_rows:
        market_value = as_float(row["current_price"]) * as_float(row["quantity"])
        enriched_stock_rows.append(
            {
                **row,
                "market_value": market_value,
                "returns_pct": _stock_returns_pct(row, as_float),
            }
        )

    stock_current = sum(as_float(row["market_value"]) for row in enriched_stock_rows)
    stock_cost = sum(as_float(row["average_price"]) * as_float(row["quantity"]) for row in enriched_stock_rows)
    mf_current = sum(as_float(row["current_value"]) for row in enriched_mf_rows)
    mf_invested = sum(_mutual_fund_invested(row, as_float) for row in enriched_mf_rows)
    total_sip = sum(as_float(row["sip"]) for row in enriched_mf_rows)
    best_stock = max(
        enriched_stock_rows,
        key=lambda row: (as_float(row["current_price"]) - as_float(row["average_price"])) * as_float(row["quantity"]),
        default=None,
    )
    best_fund = max(
        enriched_mf_rows,
        key=lambda row: as_float(row["current_value"]) - _mutual_fund_invested(row, as_float),
        default=None,
    )
    stock_section = _section(
        "stocks",
        entity_config,
        enriched_stock_rows,
        stock_current,
        "visible stock value",
        "market_value",
        [
            {"label": "Positions", "value": len(enriched_stock_rows), "note": "Tracked direct equity positions."},
            {"label": "Best stock", "value": best_stock["symbol"] if best_stock else "No data", "note": f"Rs. {((as_float(best_stock['current_price']) - as_float(best_stock['average_price'])) * as_float(best_stock['quantity'])):,.2f} P&L" if best_stock else "No stock records available."},
            {"label": "Direct gain", "value": f"Rs. {stock_current - stock_cost:,.2f}", "note": "Current stock value minus cost."},
        ],
    )
    mutual_fund_section = _section(
        "mutual_funds",
        entity_config,
        enriched_mf_rows,
        mf_current,
        "visible mutual fund value",
        "current_value",
        [
            {"label": "Funds", "value": len(enriched_mf_rows), "note": "Tracked mutual fund positions."},
            {
                "label": "Top fund",
                "value": best_fund["fund_name"] if best_fund else "No data",
                "note": (
                    f"Rs. {(as_float(best_fund['current_value']) - _mutual_fund_invested(best_fund, as_float)):,.2f} gain"
                    if best_fund
                    else "No fund records available."
                ),
            },
            {"label": "SIP load", "value": f"Rs. {total_sip:,.2f}", "note": "Recurring monthly contribution."},
        ],
    )

    if focus == "stocks":
        page_title = "Stocks"
        eyebrow = "Stocks Workspace"
        heading = "Track direct equity holdings and sync stock positions from Zerodha."
        description = "This focused view keeps stock positions, broker sync, current value, and market sensitivity together without duplicating the mutual fund page."
        chips = [
            {"label": f"{len(stock_rows)} stock positions"},
            {"label": f"Rs. {stock_current:,.2f} market value"},
            {"label": f"Rs. {stock_current - stock_cost:,.2f} direct P&L"},
        ]
        metrics = [
            {"label": "Stocks Value", "value": stock_current, "note": "Current value across direct equity positions."},
            {"label": "Invested Cost", "value": stock_cost, "note": "Average price multiplied by quantity."},
            {"label": "Direct Gain", "value": stock_current - stock_cost, "note": "Current stock value minus cost."},
        ]
        sections = [stock_section]
        nav_key = "stocks"
    elif focus == "mutual_funds":
        page_title = "Mutual Funds"
        eyebrow = "Fund Workspace"
        heading = "Track mutual fund value, returns, SIP load, and NAV refreshes in one focused view."
        description = "This page stays dedicated to mutual funds so NAV sync and fund projections do not duplicate the stocks workspace."
        chips = [
            {"label": f"{len(enriched_mf_rows)} mutual funds"},
            {"label": f"Rs. {mf_current:,.2f} current value"},
            {"label": f"Rs. {total_sip:,.2f} SIP load"},
        ]
        metrics = [
            {"label": "Mutual Funds Value", "value": mf_current, "note": "Current value across mutual funds."},
            {"label": "Invested Cost", "value": mf_invested, "note": "Invested value from amount invested or average NAV times units."},
            {"label": "Fund Gain", "value": mf_current - mf_invested, "note": "Current value minus invested capital."},
            {"label": "Monthly SIP", "value": total_sip, "note": "Recurring monthly contribution across funds."},
        ]
        sections = [mutual_fund_section]
        nav_key = "mutual_funds"
    else:
        page_title = "Stocks & Mutual Funds"
        eyebrow = "Market Workspace"
        heading = "Track direct equity and mutual funds together from one combined investment view."
        description = "This workspace brings listed holdings and mutual funds together so you can compare exposure, portfolio growth, and recurring SIP load in a single place."
        chips = [
            {"label": f"{len(stock_rows)} stock positions"},
            {"label": f"{len(enriched_mf_rows)} mutual funds"},
            {"label": f"Rs. {total_sip:,.2f} SIP load"},
        ]
        metrics = [
            {"label": "Stocks Value", "value": stock_current, "note": "Current value across direct equity positions."},
            {"label": "Mutual Funds Value", "value": mf_current, "note": "Current value across mutual funds."},
            {"label": "Combined Market Value", "value": stock_current + mf_current, "note": "Direct plus managed market exposure."},
            {"label": "Combined Gain", "value": (stock_current - stock_cost) + (mf_current - mf_invested), "note": "Current value minus invested capital."},
        ]
        sections = [stock_section, mutual_fund_section]
        nav_key = "stocks"

    return {
        "page_title": page_title,
        "eyebrow": eyebrow,
        "heading": heading,
        "description": description,
        "chips": chips,
        "metrics": metrics,
        "sections": _with_predictions(sections, as_float),
        "nav_key": nav_key,
    }


def build_outflows_workspace(
    entity_config: dict[str, Any],
    fetch_all: Callable[..., list],
    as_float: Callable[[Any], float],
) -> dict[str, Any]:
    spending_rows = fetch_all("SELECT * FROM spending ORDER BY amount DESC, id DESC")
    utility_rows = fetch_all("SELECT * FROM utility_bills ORDER BY amount DESC, id DESC")

    spending_total = sum(as_float(row["amount"]) for row in spending_rows)
    utility_total = sum(as_float(row["amount"]) for row in utility_rows)
    top_spend = max(spending_rows, key=lambda row: as_float(row["amount"]), default=None)
    top_bill = max(utility_rows, key=lambda row: as_float(row["amount"]), default=None)
    essentials = {"milk", "grocery", "medicine", "food", "electricity", "water", "gas", "internet", "fuel"}
    essential_total = sum(as_float(row["amount"]) for row in utility_rows if str(row["bill_type"]).strip().lower() in essentials)

    return {
        "page_title": "Spending & Utility Bills",
        "eyebrow": "Outflow Workspace",
        "heading": "See planned outflows and recurring household costs together from one page.",
        "description": "This workspace combines larger spending commitments and utility bills so you can understand total outflow pressure without jumping between separate pages.",
        "chips": [
            {"label": f"{len(spending_rows)} spending rows"},
            {"label": f"{len(utility_rows)} utility bills"},
            {"label": f"Rs. {spending_total + utility_total:,.2f} total outflow"},
        ],
        "metrics": [
            {"label": "Spending Total", "value": spending_total, "note": "Planned or recurring larger outflows."},
            {"label": "Utility Total", "value": utility_total, "note": "Household and everyday recurring bills."},
            {"label": "Combined Outflow", "value": spending_total + utility_total, "note": "Total burden across both groups."},
            {"label": "Essential Bills", "value": essential_total, "note": f"{(essential_total / utility_total * 100):,.2f}% of utility spend." if utility_total else "No utility data yet."},
        ],
        "sections": _with_predictions([
            _section(
                "spending",
                entity_config,
                spending_rows,
                spending_total,
                "visible spending",
                "amount",
                [
                    {"label": "Top category", "value": top_spend["spending_type"] if top_spend else "No data", "note": f"{top_spend['person']} · Rs. {as_float(top_spend['amount']):,.2f}" if top_spend else "No spending records available."},
                    {"label": "Recipients", "value": len({row['recipient'] for row in spending_rows}), "note": "Distinct recipients in spending rows."},
                    {"label": "Average spend", "value": f"Rs. {(spending_total / len(spending_rows)):,.2f}" if spending_rows else "Rs. 0.00", "note": "Average spending row amount."},
                ],
            ),
            _section(
                "utility_bills",
                entity_config,
                utility_rows,
                utility_total,
                "visible utility spend",
                "amount",
                [
                    {"label": "Highest bill", "value": top_bill["bill_type"] if top_bill else "No data", "note": f"Rs. {as_float(top_bill['amount']):,.2f}" if top_bill else "No utility records available."},
                    {"label": "Essential spend", "value": f"Rs. {essential_total:,.2f}", "note": "Core household categories only."},
                    {"label": "Bill types", "value": len({row['bill_type'] for row in utility_rows}), "note": "Distinct bill categories tracked."},
                ],
            ),
        ], as_float),
        "nav_key": "spending",
    }


def build_capital_workspace(
    entity_config: dict[str, Any],
    fetch_all: Callable[..., list],
    as_float: Callable[[Any], float],
) -> dict[str, Any]:
    capital_rows = fetch_all("SELECT * FROM loans ORDER BY ABS(amount) DESC, id DESC")
    earnings_rows = fetch_all("SELECT * FROM earnings ORDER BY amount DESC, id DESC")

    receivables = sum(as_float(row["amount"]) for row in capital_rows if as_float(row["amount"]) > 0)
    liabilities = sum(abs(as_float(row["amount"])) for row in capital_rows if as_float(row["amount"]) < 0)
    earnings_total = sum(as_float(row["amount"]) for row in earnings_rows)
    top_capital = max(capital_rows, key=lambda row: abs(as_float(row["amount"])), default=None)
    top_income = max(earnings_rows, key=lambda row: as_float(row["amount"]), default=None)

    return {
        "page_title": "Capital & Earnings",
        "eyebrow": "Income Capital Workspace",
        "heading": "Keep capital positions and income streams together in one financial control view.",
        "description": "This workspace pairs deployed capital with recurring earnings so you can compare income generation, obligations, and overall financial inflow strength side by side.",
        "chips": [
            {"label": f"{len(capital_rows)} capital rows"},
            {"label": f"{len(earnings_rows)} earning rows"},
            {"label": f"Rs. {earnings_total:,.2f} earnings total"},
        ],
        "metrics": [
            {"label": "Receivables", "value": receivables, "note": "Capital expected back or earning interest."},
            {"label": "Liabilities", "value": liabilities, "note": "Capital currently owed."},
            {"label": "Net Capital", "value": receivables - liabilities, "note": "Receivables minus liabilities."},
            {"label": "Earnings Total", "value": earnings_total, "note": "Recurring income across all sources."},
        ],
        "sections": _with_predictions([
            _section(
                "loans",
                entity_config,
                capital_rows,
                receivables - liabilities,
                "visible net capital",
                "amount",
                [
                    {"label": "Largest position", "value": top_capital["borrower"] if top_capital else "No data", "note": f"Rs. {abs(as_float(top_capital['amount'])):,.2f}" if top_capital else "No capital records available."},
                    {"label": "Receivable rows", "value": sum(1 for row in capital_rows if as_float(row["amount"]) > 0), "note": "Positive capital positions."},
                    {"label": "Liability rows", "value": sum(1 for row in capital_rows if as_float(row["amount"]) < 0), "note": "Negative capital positions."},
                ],
            ),
            _section(
                "earnings",
                entity_config,
                earnings_rows,
                earnings_total,
                "visible earnings",
                "amount",
                [
                    {"label": "Top income line", "value": top_income["source"] if top_income else "No data", "note": f"{top_income['person']} · Rs. {as_float(top_income['amount']):,.2f}" if top_income else "No earnings records available."},
                    {"label": "Income types", "value": len({row['income_type'] for row in earnings_rows}), "note": "Distinct earning categories."},
                    {"label": "Average income", "value": f"Rs. {(earnings_total / len(earnings_rows)):,.2f}" if earnings_rows else "Rs. 0.00", "note": "Average earning row amount."},
                ],
            ),
        ], as_float),
        "nav_key": "loans",
    }
