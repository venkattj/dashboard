from __future__ import annotations

from typing import Any, Callable

from flask import render_template

from .workspaces import build_markets_workspace


def register_mutual_funds_routes(
    app,
    entity_config: dict[str, Any],
    fetch_all: Callable[..., list],
    as_float: Callable[[Any], float],
) -> None:
    @app.get("/entity/mutual_funds", endpoint="mutual_funds_page")
    def mutual_funds_page() -> str:
        return render_template(
            "paired_workspace.html",
            **build_markets_workspace(entity_config=entity_config, fetch_all=fetch_all, as_float=as_float),
        )
