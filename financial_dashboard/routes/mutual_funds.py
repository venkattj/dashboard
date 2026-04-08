from __future__ import annotations

from datetime import datetime
from typing import Any, Callable

import requests
from flask import flash, redirect, render_template, url_for

from .workspaces import build_markets_workspace

MF_API_BASE_URL = "https://api.mfapi.in/mf"

# Optional helper mapping when the workbook does not store scheme codes.
# Add entries like {"Fund Name": "123456"} if you prefer auto-matching by name.
MUTUAL_FUND_SCHEMES: dict[str, str] = {}


def fetch_latest_nav(scheme_code: str) -> dict[str, Any] | None:
    try:
        response = requests.get(f"{MF_API_BASE_URL}/{scheme_code}", timeout=12)
        response.raise_for_status()
        payload = response.json()
        entries = payload.get("data")
        if not entries:
            return None
        latest = entries[0]
        raw_nav = latest.get("nav")
        if not raw_nav:
            return None
        nav_value = float(str(raw_nav).replace(",", "").strip())
        return {"nav": nav_value}
    except (requests.RequestException, ValueError, KeyError, IndexError, TypeError):
        return None


def resolve_scheme_code(row: dict[str, Any]) -> str | None:
    fund_name = str(row.get("fund_name", "")).strip()
    scheme_candidate = row.get("scheme_code") or MUTUAL_FUND_SCHEMES.get(fund_name)
    if not scheme_candidate:
        return None
    return str(scheme_candidate).strip()


def register_mutual_funds_routes(
    app,
    entity_config: dict[str, Any],
    fetch_all: Callable[..., list],
    execute: Callable[..., None],
    as_float: Callable[[Any], float],
) -> None:
    def _parse_nav_synced(value: Any) -> datetime | None:
        if isinstance(value, datetime):
            return value
        if value is None:
            return None
        candidate = str(value).strip()
        if not candidate:
            return None
        try:
            return datetime.fromisoformat(candidate)
        except ValueError:
            try:
                return datetime.strptime(candidate, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                return None

    @app.get("/entity/mutual_funds", endpoint="mutual_funds_page")
    def mutual_funds_page() -> str:
        mf_rows = fetch_all("SELECT * FROM mutual_funds ORDER BY latest_nav * units DESC, id DESC")
        workspace = build_markets_workspace(
            entity_config=entity_config,
            fetch_all=fetch_all,
            as_float=as_float,
            mutual_fund_rows=mf_rows,
        )
        last_sync_candidates = [
            parsed
            for row in mf_rows
            if (parsed := _parse_nav_synced(row.get("nav_synced_at")))
        ]
        last_sync_at = max(last_sync_candidates) if last_sync_candidates else None
        integration_panel = {
            "mode": "mutual_funds",
            "provider": "mfapi.in",
            "sync_url": url_for("mutual_funds_sync_nav"),
            "fund_count": len(mf_rows),
            "schemes_configured": sum(1 for row in mf_rows if row.get("scheme_code")),
            "last_sync_at": last_sync_at.strftime("%Y-%m-%d %H:%M:%S") if last_sync_at else None,
        }
        return render_template("paired_workspace.html", integration_panel=integration_panel, **workspace)

    @app.post("/mutual-funds/nav/sync", endpoint="mutual_funds_sync_nav")
    def mutual_funds_sync_nav() -> Any:
        rows = fetch_all("SELECT * FROM mutual_funds ORDER BY fund_name")
        nav_cache: dict[str, dict[str, Any] | None] = {}
        errors: list[str] = []
        updated = 0
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for row in rows:
            scheme_code = resolve_scheme_code(row)
            if not scheme_code:
                continue
            nav_data = nav_cache.get(scheme_code)
            if nav_data is None:
                nav_data = fetch_latest_nav(scheme_code)
                nav_cache[scheme_code] = nav_data
            if not nav_data:
                errors.append(f"{row['fund_name']} ({scheme_code})")
                continue

            nav_value = nav_data["nav"]
            units = max(as_float(row.get("units")), 0.0)

            execute(
                """
                UPDATE `mutual_funds`
                SET `units` = ?, `latest_nav` = ?, `nav_synced_at` = ?
                WHERE `id` = ?
                """,
                (units, nav_value, now_str, row["id"]),
            )
            updated += 1

        if updated:
            flash(f"Updated NAV for {updated} mutual fund{'s' if updated != 1 else ''}.", "success")
        else:
            flash("No mutual fund rows could be matched to a scheme code for NAV sync.", "warning")

        if errors:
            flash(
                f"Could not fetch NAV for {len(errors)} fund(s): {', '.join(errors)}. "
                "Verify the scheme codes or try again later.",
                "error" if not updated else "warning",
            )

        return redirect(url_for("mutual_funds_page"))
