from __future__ import annotations

from typing import Any, Callable

from flask import render_template

from .workspaces import build_outflows_workspace


def register_utility_bills_routes(
    app,
    entity_config: dict[str, Any],
    fetch_all: Callable[..., list],
    as_float: Callable[[Any], float],
) -> None:
    @app.get("/entity/utility_bills", endpoint="utility_bills_page")
    def utility_bills_page() -> str:
        return render_template(
            "paired_workspace.html",
            **build_outflows_workspace(entity_config=entity_config, fetch_all=fetch_all, as_float=as_float),
        )
