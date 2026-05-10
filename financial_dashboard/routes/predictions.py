from __future__ import annotations

from typing import Any, Callable


MONTH_STEPS = (0, 3, 6, 9, 12)


def _point(label: str, amount: float, peak: float) -> dict[str, Any]:
    height = (abs(amount) / peak * 100) if peak else 0
    return {"label": label, "amount": amount, "height": max(height, 4 if amount else 0)}


def build_prediction_graph(
    title: str,
    note: str,
    current_value: float = 0.0,
    monthly_delta: float = 0.0,
    annual_rate_pct: float = 0.0,
    cumulative: bool = False,
) -> dict[str, Any]:
    amounts = []
    monthly_rate = annual_rate_pct / 100 / 12
    for month in MONTH_STEPS:
        if cumulative:
            amount = monthly_delta * month
        else:
            amount = current_value * ((1 + monthly_rate) ** month) + (monthly_delta * month)
        amounts.append(amount)

    peak = max((abs(amount) for amount in amounts), default=1) or 1
    return {
        "title": title,
        "note": note,
        "points": [_point("Now" if month == 0 else f"{month}M", amount, peak) for month, amount in zip(MONTH_STEPS, amounts)],
        "current_value": amounts[0] if amounts else current_value,
        "projected_value": amounts[-1] if amounts else current_value,
        "delta": (amounts[-1] - amounts[0]) if amounts else 0.0,
    }


def build_entity_prediction(
    entity_key: str,
    rows: list[dict[str, Any]],
    total: float,
    as_float: Callable[[Any], float],
) -> dict[str, Any]:
    if entity_key == "earnings":
        return build_prediction_graph(
            "Income Run-Rate",
            "Cumulative income implied by the current monthly earnings rows.",
            monthly_delta=total,
            cumulative=True,
        )
    if entity_key in {"spending", "utility_bills"}:
        return build_prediction_graph(
            "Outflow Run-Rate",
            "Cumulative commitment implied by the current monthly outflow rows.",
            monthly_delta=total,
            cumulative=True,
        )
    if entity_key == "mutual_funds":
        sip_total = sum(as_float(row.get("sip")) for row in rows)
        return build_prediction_graph(
            "SIP Projection",
            "Current fund value plus scheduled SIP contributions; market movement is not assumed.",
            current_value=total,
            monthly_delta=sip_total,
        )
    if entity_key == "stocks":
        return build_prediction_graph(
            "Market Sensitivity",
            "A simple 6% annual scenario on current market value for planning sensitivity.",
            current_value=total,
            annual_rate_pct=6,
        )
    if entity_key == "fixed_deposits":
        invested = sum(as_float(row.get("invested")) for row in rows)
        weighted_rate = (
            sum(as_float(row.get("interest_rate")) * as_float(row.get("current_amount", row.get("invested"))) for row in rows) / total
            if total
            else 0
        )
        return build_prediction_graph(
            "FD Accrual",
            f"Current FD value grown at the weighted listed rate of {weighted_rate:.2f}%.",
            current_value=total or invested,
            annual_rate_pct=weighted_rate,
        )
    if entity_key == "loans":
        receivable = sum(as_float(row.get("amount")) for row in rows if as_float(row.get("amount")) > 0)
        owed = sum(abs(as_float(row.get("amount"))) for row in rows if as_float(row.get("amount")) < 0)
        return build_prediction_graph(
            "Net Capital",
            "Current receivables minus obligations held flat as a 12-month planning base.",
            current_value=receivable - owed,
        )
    if entity_key in {"standard_chits", "variable_chits", "variable_chit_payments"}:
        monthly_commitment = sum(as_float(row.get("emi", row.get("amount"))) for row in rows)
        return build_prediction_graph(
            "Chit Commitment",
            "Cumulative scheduled chit load based on current EMI/payment rows.",
            monthly_delta=monthly_commitment,
            cumulative=True,
        )
    return build_prediction_graph(
        "12M Planning View",
        "Current value held flat as a baseline for review and manual updates.",
        current_value=total,
    )


def build_overall_prediction(
    net_worth: float,
    monthly_surplus: float,
) -> dict[str, Any]:
    return build_prediction_graph(
        "Overall Net Worth Projection",
        "Current net worth plus the present monthly surplus run-rate over the next year.",
        current_value=net_worth,
        monthly_delta=monthly_surplus,
    )
