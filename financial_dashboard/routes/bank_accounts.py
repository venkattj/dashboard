from __future__ import annotations

from typing import Any, Callable

from flask import flash, redirect, render_template, request, url_for

from .workspaces import build_banking_workspace


def register_bank_account_routes(
    app,
    entity_config: dict[str, Any],
    fetch_all: Callable[..., list],
    fetch_one: Callable[..., dict | None],
    execute: Callable[..., None],
    as_float: Callable[[Any], float],
    ensure_bank_account_entities: Callable[[str, str], tuple[int, int]],
) -> None:
    @app.get("/entity/bank_accounts", endpoint="bank_accounts_page")
    def bank_accounts_page() -> str:
        return render_template(
            "paired_workspace.html",
            **build_banking_workspace(entity_config=entity_config, fetch_all=fetch_all, as_float=as_float),
        )

    @app.post("/entity/bank_accounts/<int:row_id>/inline-update", endpoint="bank_account_inline_update")
    def bank_account_inline_update(row_id: int):
        values = {
            "account_holder": request.form.get("account_holder", "").strip(),
            "bank_name": request.form.get("bank_name", "").strip(),
            "balance": as_float(request.form.get("balance", "0")),
            "purpose": request.form.get("purpose", "").strip(),
        }
        user_id, bank_id = ensure_bank_account_entities(values["account_holder"], values["bank_name"])
        execute(
            "UPDATE bank_accounts SET user_id = ?, bank_id = ?, balance = ?, purpose = ? WHERE id = ?",
            (user_id, bank_id, values["balance"], values["purpose"], row_id),
        )
        flash("Bank account row updated.", "success")

        query_args = {
            "q": request.form.get("q", "").strip(),
            "holder": request.form.get("holder", "").strip(),
            "purpose": request.form.get("purpose_filter", "").strip(),
            "min_balance": request.form.get("min_balance", "").strip(),
            "max_balance": request.form.get("max_balance", "").strip(),
            "sort_by": request.form.get("sort_by", "balance").strip(),
            "sort_dir": request.form.get("sort_dir", "desc").strip(),
        }
        return redirect(url_for("bank_accounts_page", **query_args))
