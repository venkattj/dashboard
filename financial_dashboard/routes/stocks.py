from __future__ import annotations

from typing import Any, Callable

from flask import render_template, url_for

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
        workspace = build_markets_workspace(entity_config=entity_config, fetch_all=fetch_all, as_float=as_float)
        mutual_section = next((section for section in workspace.get("sections", []) if section["entity_key"] == "mutual_funds"), None)
        mutual_rows = mutual_section["rows"] if mutual_section else []
        last_sync_candidates = [row["nav_synced_at"] for row in mutual_rows if row.get("nav_synced_at")]
        last_sync_at = max(last_sync_candidates) if last_sync_candidates else None
        if last_sync_at and hasattr(last_sync_at, "strftime"):
            mutual_last_sync = last_sync_at.strftime("%Y-%m-%d %H:%M:%S")
        else:
            mutual_last_sync = str(last_sync_at) if last_sync_at else None
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
                "mutual_fund_sync_url": url_for("mutual_funds_sync_nav"),
                "mutual_fund_count": len(mutual_rows),
                "mutual_fund_schemes_configured": sum(1 for row in mutual_rows if row.get("scheme_code")),
                "mutual_fund_last_sync_at": mutual_last_sync,
            },
            **workspace,
        )
