from __future__ import annotations

from datetime import date
from typing import Any, Callable

from flask import render_template


def _days_until(target: Any) -> int | None:
    if not target:
        return None
    if isinstance(target, date):
        return (target - date.today()).days
    return None


def build_chits_page_context(
    fetch_all: Callable[..., list],
    as_float: Callable[[Any], float],
    as_int: Callable[[Any], int],
) -> dict[str, Any]:
    standard_rows = fetch_all("SELECT * FROM standard_chits ORDER BY current_value DESC, id DESC")
    variable_rows = fetch_all("SELECT * FROM variable_chits ORDER BY net_value DESC, id DESC")
    payment_rows = fetch_all("SELECT * FROM variable_chit_payments ORDER BY emi_no ASC, id ASC")

    standard_enriched = []
    for row in standard_rows:
        duration = max(as_int(row["duration_months"]), 0)
        paid_months = max(as_int(row["paid_months"]), 0)
        completion_pct = (paid_months / duration * 100) if duration else 0
        standard_enriched.append(
            {
                **row,
                "remaining_months": max(duration - paid_months, 0),
                "completion_pct": min(completion_pct, 100),
                "days_to_maturity": _days_until(row["maturity_date"]),
                "chit_type": "Standard",
                "exposure_value": as_float(row["current_value"]),
                "display_name": row["organization"],
            }
        )

    variable_enriched = []
    for row in variable_rows:
        months = max(as_int(row["months"]), 0)
        emi_paid = max(as_int(row["emi_paid"]), 0)
        progress_pct = (emi_paid / months * 100) if months else 0
        variable_enriched.append(
            {
                **row,
                "remaining_emis": max(months - emi_paid, 0),
                "progress_pct": min(progress_pct, 100),
                "days_to_maturity": _days_until(row["maturity_date"]),
                "chit_type": "Variable",
                "exposure_value": as_float(row["net_value"]),
                "display_name": row["name"],
            }
        )

    payment_enriched = []
    for row in payment_rows:
        scheduled = as_float(row["amount"])
        actual_paid = row["actual_paid"]
        actual_value = as_float(actual_paid) if actual_paid is not None else 0
        payment_enriched.append(
            {
                **row,
                "status": "Paid" if actual_paid is not None else "Pending",
                "variance": actual_value - scheduled if actual_paid is not None else 0,
            }
        )

    total_standard_current = sum(as_float(row["current_value"]) for row in standard_enriched)
    total_variable_net = sum(as_float(row["net_value"]) for row in variable_enriched)
    total_chit_value = total_standard_current + total_variable_net
    total_standard_emi = sum(as_float(row["emi"]) for row in standard_enriched)
    total_variable_paid = sum(as_float(row["total_paid"]) for row in variable_enriched)

    pending_payments = [row for row in payment_enriched if row["status"] == "Pending"]
    paid_payments = [row for row in payment_enriched if row["status"] == "Paid"]
    pending_payment_total = sum(as_float(row["amount"]) for row in pending_payments)
    paid_payment_total = sum(as_float(row["actual_paid"]) for row in paid_payments)

    maturity_candidates = [
        row for row in (standard_enriched + variable_enriched) if row["days_to_maturity"] is not None
    ]
    next_maturity = min(maturity_candidates, key=lambda row: row["days_to_maturity"], default=None)
    largest_chit = max(
        standard_enriched + variable_enriched,
        key=lambda row: as_float(row["exposure_value"]),
        default=None,
    )

    concentration = sorted(
        standard_enriched + variable_enriched,
        key=lambda row: as_float(row["exposure_value"]),
        reverse=True,
    )
    largest_exposure = concentration[0]["exposure_value"] if concentration else 1

    return {
        "standard_rows": standard_enriched,
        "variable_rows": variable_enriched,
        "payment_rows": payment_enriched,
        "insights": {
            "standard_count": len(standard_enriched),
            "variable_count": len(variable_enriched),
            "payment_count": len(payment_enriched),
            "total_chit_value": total_chit_value,
            "total_standard_current": total_standard_current,
            "total_variable_net": total_variable_net,
            "total_standard_emi": total_standard_emi,
            "total_variable_paid": total_variable_paid,
            "pending_payment_count": len(pending_payments),
            "pending_payment_total": pending_payment_total,
            "paid_payment_total": paid_payment_total,
            "next_maturity": next_maturity,
            "largest_chit": largest_chit,
            "concentration": concentration[:8],
            "largest_exposure": largest_exposure,
        },
    }


def register_chits_routes(
    app,
    entity_config: dict[str, Any],
    fetch_all: Callable[..., list],
    as_float: Callable[[Any], float],
    as_int: Callable[[Any], int],
) -> None:
    def render_chits_page() -> str:
        context = build_chits_page_context(fetch_all=fetch_all, as_float=as_float, as_int=as_int)
        return render_template(
            "chits.html",
            entity_key="standard_chits",
            entity=entity_config["standard_chits"],
            nav_key="standard_chits",
            **context,
        )

    @app.get("/entity/standard_chits", endpoint="standard_chits_page")
    def standard_chits_page() -> str:
        return render_chits_page()

    @app.get("/entity/variable_chits", endpoint="variable_chits_page")
    def variable_chits_page() -> str:
        return render_chits_page()

    @app.get("/entity/variable_chit_payments", endpoint="variable_chit_payments_page")
    def variable_chit_payments_page() -> str:
        return render_chits_page()
