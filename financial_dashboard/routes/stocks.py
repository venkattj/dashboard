from __future__ import annotations

from typing import Any, Callable

from flask import render_template

from .workspaces import build_markets_workspace


def register_stocks_routes(
    app,
    entity_config: dict[str, Any],
    fetch_all: Callable[..., list],
    as_float: Callable[[Any], float],
    get_current_user: Callable[[], dict[str, Any] | None],
    zerodha_login_url: Callable[[str, int], str],
    zerodha_redirect_uri: Callable[[], str],
) -> None:
    @app.get("/entity/stocks", endpoint="stocks_page")
    def stocks_page() -> str:
        user = get_current_user() or {}
        api_key = (user.get("zerodha_api_key") or "").strip()
        access_token = (user.get("zerodha_access_token") or "").strip()
        workspace = build_markets_workspace(
            entity_config=entity_config,
            fetch_all=fetch_all,
            as_float=as_float,
            focus="stocks",
        )
        return render_template(
            "paired_workspace.html",
            integration_panel={
                "provider": "Zerodha",
                "mode": "stocks",
                "api_key": api_key,
                "redirect_uri": zerodha_redirect_uri(),
                "connected": bool(access_token),
                "user_name": user.get("zerodha_user_name"),
                "user_id": user.get("zerodha_user_id"),
                "connected_at": user.get("zerodha_connected_at"),
                "last_sync_at": user.get("zerodha_last_sync_at"),
                "login_url": zerodha_login_url(api_key, user.get("id")) if api_key and user.get("id") else None,
            },
            **workspace,
        )
