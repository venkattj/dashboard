from __future__ import annotations

from datetime import date
from typing import Any, Callable

from flask import render_template


def build_sneha_payments_page_context(
    fetch_all: Callable[..., list],
    as_float: Callable[[Any], float],
) -> dict[str, Any]:
    rows = fetch_all("SELECT * FROM sneha_payments ORDER BY payment_date ASC, id ASC")

    total_paid = sum(as_float(row["amount"]) for row in rows)
    average_payment = (total_paid / len(rows)) if rows else 0
    latest_payment = rows[-1] if rows else None
    highest_payment = max(rows, key=lambda row: as_float(row["amount"]), default=None)

    known_balances = [row for row in rows if row["principal_balance"] is not None]
    latest_balance = known_balances[-1] if known_balances else None

    paid_this_year = 0.0
    current_year = date.today().year
    for row in rows:
        payment_date = row["payment_date"]
        if isinstance(payment_date, date) and payment_date.year == current_year:
            paid_this_year += as_float(row["amount"])

    month_mix: dict[str, float] = {}
    for row in rows:
        payment_date = row["payment_date"]
        label = payment_date.strftime("%b %Y") if isinstance(payment_date, date) else str(payment_date)
        month_mix[label] = month_mix.get(label, 0) + as_float(row["amount"])

    payment_mix = [{"label": key, "amount": value} for key, value in month_mix.items()]
    payment_mix.sort(key=lambda item: item["label"])
    largest_mix_value = max((item["amount"] for item in payment_mix), default=1) or 1

    return {
        "rows": rows,
        "insights": {
            "entry_count": len(rows),
            "total_paid": total_paid,
            "average_payment": average_payment,
            "latest_payment": latest_payment,
            "highest_payment": highest_payment,
            "latest_balance": latest_balance,
            "paid_this_year": paid_this_year,
            "payment_mix": payment_mix,
            "largest_mix_value": largest_mix_value,
        },
    }


def register_sneha_payments_routes(
    app,
    entity_config: dict[str, Any],
    fetch_all: Callable[..., list],
    as_float: Callable[[Any], float],
) -> None:
    @app.get("/entity/sneha_payments", endpoint="sneha_payments_page")
    def sneha_payments_page() -> str:
        entity = entity_config["sneha_payments"]
        context = build_sneha_payments_page_context(fetch_all=fetch_all, as_float=as_float)
        return render_template(
            "sneha_payments.html",
            entity_key="sneha_payments",
            entity=entity,
            **context,
        )
