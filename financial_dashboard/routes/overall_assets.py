from __future__ import annotations

from typing import Any, Callable

from flask import render_template


def build_overall_assets_page_context(
    fetch_all: Callable[..., list],
    as_float: Callable[[Any], float],
) -> dict[str, Any]:
    rows = fetch_all("SELECT * FROM overall_assets ORDER BY amount DESC, id DESC")

    total_assets = sum(as_float(row["amount"]) for row in rows)
    average_asset = (total_assets / len(rows)) if rows else 0
    largest_asset = max(rows, key=lambda row: as_float(row["amount"]), default=None)
    smallest_asset = min(rows, key=lambda row: as_float(row["amount"]), default=None)

    note_count = sum(1 for row in rows if row["note"])
    asset_mix = [{"label": row["label"], "amount": as_float(row["amount"])} for row in rows]
    largest_mix_value = max((item["amount"] for item in asset_mix), default=1) or 1

    return {
        "rows": rows,
        "insights": {
            "entry_count": len(rows),
            "total_assets": total_assets,
            "average_asset": average_asset,
            "largest_asset": largest_asset,
            "smallest_asset": smallest_asset,
            "note_count": note_count,
            "asset_mix": asset_mix[:10],
            "largest_mix_value": largest_mix_value,
        },
    }


def register_overall_assets_routes(
    app,
    entity_config: dict[str, Any],
    fetch_all: Callable[..., list],
    as_float: Callable[[Any], float],
) -> None:
    @app.get("/entity/overall_assets", endpoint="overall_assets_page")
    def overall_assets_page() -> str:
        entity = entity_config["overall_assets"]
        context = build_overall_assets_page_context(fetch_all=fetch_all, as_float=as_float)
        return render_template(
            "overall_assets.html",
            entity_key="overall_assets",
            entity=entity,
            **context,
        )
