from __future__ import annotations

from typing import Any, Callable

from flask import flash, redirect, render_template, request, url_for

from .workspaces import build_banking_workspace


def register_fixed_deposit_routes(
    app,
    entity_config: dict[str, Any],
    fetch_all: Callable[..., list],
    execute: Callable[..., None],
    as_float: Callable[[Any], float],
    as_int: Callable[[Any], int],
) -> None:
    @app.get("/entity/fixed_deposits", endpoint="fixed_deposits_page")
    def fixed_deposits_page() -> str:
        return render_template(
            "paired_workspace.html",
            **build_banking_workspace(entity_config=entity_config, fetch_all=fetch_all, as_float=as_float),
        )

    @app.post("/entity/fixed_deposits/<int:row_id>/inline-update", endpoint="fixed_deposit_inline_update")
    def fixed_deposit_inline_update(row_id: int):
        values = {
            "bank": request.form.get("bank", "").strip(),
            "invested": as_float(request.form.get("invested", "0")),
            "interest_rate": as_float(request.form.get("interest_rate", "0")),
            "maturity_date": request.form.get("maturity_date", "").strip(),
            "created_date": request.form.get("created_date", "").strip(),
            "current_amount": as_float(request.form.get("current_amount", "0")),
            "days_to_mature": as_int(request.form.get("days_to_mature", "0")),
        }
        execute(
            "UPDATE fixed_deposits SET bank = ?, invested = ?, interest_rate = ?, maturity_date = ?, created_date = ?, current_amount = ?, days_to_mature = ? WHERE id = ?",
            (
                values["bank"],
                values["invested"],
                values["interest_rate"],
                values["maturity_date"],
                values["created_date"],
                values["current_amount"],
                values["days_to_mature"],
                row_id,
            ),
        )
        flash("Fixed deposit row updated.", "success")
        return redirect(url_for("fixed_deposits_page"))
