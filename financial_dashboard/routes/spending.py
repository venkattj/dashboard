from __future__ import annotations

from typing import Any, Callable

from flask import render_template

from .workspaces import build_outflows_workspace


def register_spending_routes(
    app,
    entity_config: dict[str, Any],
    fetch_all: Callable[..., list],
    as_float: Callable[[Any], float],
) -> None:
    @app.get("/entity/spending", endpoint="spending_page")
    def spending_page() -> str:
        return render_template(
            "paired_workspace.html",
            **build_outflows_workspace(entity_config=entity_config, fetch_all=fetch_all, as_float=as_float),
        )
