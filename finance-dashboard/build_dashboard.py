import argparse
import json
import html
from pathlib import Path

import pandas as pd


def safe_numeric(series):
    return pd.to_numeric(series, errors="coerce").fillna(0.0)


def load_sheet(path, sheet_name):
    try:
        return pd.read_excel(path, sheet_name=sheet_name)
    except Exception:
        return pd.DataFrame()


def sample_rows(df, columns, limit=6, sort_by=None, numeric_sort=True):
    if df.empty:
        return []
    subset = df
    if sort_by and sort_by in df.columns:
        subset = df.sort_values(by=sort_by, ascending=False)
    rows = []
    for _, row in subset.head(limit).iterrows():
        entry = {}
        for col in columns:
            if col in df.columns:
                entry[col] = row[col]
        rows.append(entry)
    return rows


def format_currency(value):
    if pd.isna(value):
        return "-"
    try:
        return f"₹{float(value):,.0f}"
    except (ValueError, TypeError):
        return html.escape(str(value)) if value is not None else "-"


def summarize_earnings(df):
    earnings = []
    if df.empty:
        return earnings
    for col in df.columns:
        if col.lower().startswith("unnamed"):
            continue
        total = float(safe_numeric(df[col]).sum())
        if total and total != 0.0:
            earnings.append({"label": col, "amount": total})
    return earnings


def summarize_assets(banks, fixed, stocks, mutual, standard, variable):
    bank_total = float(safe_numeric(banks["balance"]).sum()) if "balance" in banks else 0.0
    fd_current = (
        float(safe_numeric(fixed["Current Amount"]).sum())
        if "Current Amount" in fixed
        else 0.0
    )
    stock_current = (
        float(safe_numeric(stocks["current"]).sum()) if "current" in stocks else 0.0
    )
    mutual_current = (
        float(safe_numeric(mutual["Current"]).sum()) if "Current" in mutual else 0.0
    )
    chit_standard = (
        float(safe_numeric(standard["Current_value"]).sum())
        if "Current_value" in standard
        else 0.0
    )
    chit_variable = (
        float(safe_numeric(variable["net_value"]).sum())
        if "net_value" in variable
        else 0.0
    )
    asset_breakdown = [
        {"label": "Banks", "amount": bank_total},
        {"label": "Fixed Deposits", "amount": fd_current},
        {"label": "Stocks", "amount": stock_current},
        {"label": "Mutual Funds", "amount": mutual_current},
        {"label": "Chits", "amount": chit_standard + chit_variable},
    ]
    total_assets = sum(item["amount"] for item in asset_breakdown)
    return asset_breakdown, total_assets


def build_dashboard_data(source):
    banks = load_sheet(source, "bank_accounts")
    bank_lookup = load_sheet(source, "Banks")
    fixed = load_sheet(source, "Fixed Deposit")
    stocks = load_sheet(source, "Stocks")
    mutual = load_sheet(source, "Mutal Funds")
    standard_chits = load_sheet(source, "Standard_Chits")
    variable_chits = load_sheet(source, "Variable_Chit")
    spending = load_sheet(source, "Spending")
    utility = load_sheet(source, "Utility Bills")
    earnings = load_sheet(source, "Sheet1")
    overall = load_sheet(source, "Overall")
    loans = load_sheet(source, "Loans")

    if not banks.empty and "bank_id" in banks.columns and not bank_lookup.empty:
        banks = banks.merge(
            bank_lookup[["id", "name"]],
            left_on="bank_id",
            right_on="id",
            how="left",
            suffixes=("", "_bank"),
        )

    banks["balance"] = safe_numeric(banks["balance"]) if "balance" in banks else pd.Series(dtype=float)

    asset_breakdown, total_assets = summarize_assets(
        banks, fixed, stocks, mutual, standard_chits, variable_chits
    )

    spending_breakdown = []
    if not spending.empty and "Amount" in spending.columns:
        spending_breakdown.append(
            {"label": "Spendings", "amount": float(safe_numeric(spending["Amount"]).sum())}
        )
    if not utility.empty and "Amount" in utility.columns:
        spending_breakdown.append(
            {"label": "Utility Bills", "amount": float(safe_numeric(utility["Amount"]).sum())}
        )

    earnings_breakdown = summarize_earnings(earnings)

    loans_out = (
        float(safe_numeric(loans.loc[loans["Amount"] > 0, "Amount"]).sum())
        if "Amount" in loans.columns
        else 0.0
    )
    loans_liability = (
        float(safe_numeric(loans.loc[loans["Amount"] < 0, "Amount"]).sum())
        if "Amount" in loans.columns
        else 0.0
    )

    overall_rows = []
    if not overall.empty:
        label_col = "Label" if "Label" in overall.columns else overall.columns[0]
        amount_col = "Amount" if "Amount" in overall.columns else overall.columns[1]
        for _, row in overall.iterrows():
            label = row.get(label_col)
            amount = row.get(amount_col)
            if pd.notna(label):
                overall_rows.append({"label": label, "amount": float(safe_numeric(pd.Series([amount])).iloc[0])})

    return {
        "totals": {
            "bank_balance": asset_breakdown[0]["amount"],
            "fixed_deposits": asset_breakdown[1]["amount"],
            "stocks": asset_breakdown[2]["amount"],
            "mutual_funds": asset_breakdown[3]["amount"],
            "chits": asset_breakdown[4]["amount"],
            "total_assets": total_assets,
            "loan_out": loans_out,
            "loan_liability": loans_liability,
            "net_worth": total_assets + loans_liability,
        },
        "asset_breakdown": asset_breakdown,
        "spending_breakdown": spending_breakdown,
        "earnings": earnings_breakdown,
        "banks": sample_rows(
            banks,
            columns=["name", "purpose", "balance", "user_id"],
            sort_by="balance",
        ),
        "fixed_deposits": sample_rows(
            fixed,
            columns=["account_id", "Invested", "Current Amount", "Days To Mature"],
        ),
        "stocks": sample_rows(
            stocks,
            columns=["Symbol", "Exchange", "Invested", "current", "Source"],
            sort_by="current",
        ),
        "mutual_funds": sample_rows(
            mutual, columns=["id", "Invested", "Current"], sort_by="Current"
        ),
        "standard_chits": sample_rows(
            standard_chits, columns=["Organsation", "Current_value", "Unnamed: 9"]
        ),
        "variable_chits": sample_rows(
            variable_chits, columns=["Name", "net_value", "emi_paid"]
        ),
        "spending_rows": sample_rows(
            spending,
            columns=["Spending Type", "Amount", "Person", "Recipient"],
            sort_by="Amount",
        ),
        "utility_rows": sample_rows(utility, columns=["Type", "Amount"]),
        "overall_rows": overall_rows,
    }


def render_rows(rows, columns):
    if not rows:
        return '<tr><td colspan="4">No data available</td></tr>'
    html_rows = []
    for row in rows:
        cells = []
        for col in columns:
            value = row.get(col)
            cell = format_currency(value) if isinstance(value, (int, float)) else html.escape(str(value)) if value not in (None, "") else "-"
            cells.append(f"<td>{cell}</td>")
        html_rows.append(f"<tr>{''.join(cells)}</tr>")
    return "\n".join(html_rows)


def render_dashboard(data, output):
    asset_labels = [item["label"] for item in data["asset_breakdown"]]
    asset_values = [item["amount"] for item in data["asset_breakdown"]]
    spending_labels = [item["label"] for item in data["spending_breakdown"]]
    spending_values = [item["amount"] for item in data["spending_breakdown"]]
    earnings_labels = [item["label"] for item in data["earnings"]]
    earnings_values = [item["amount"] for item in data["earnings"]]

    html_content = f"""
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Expanded Financial Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
      :root {{
        color-scheme: dark;
      }}
      body {{
        font-family: 'Segoe UI', system-ui, sans-serif;
        margin: 0;
        min-height: 100vh;
        background: #030712;
        color: #e2e8f0;
      }}
      main {{
        max-width: 1200px;
        margin: 0 auto;
        padding: 32px 24px 48px;
      }}
      h1 {{
        margin-bottom: 4px;
      }}
      h2 {{
        margin-top: 0;
      }}
      .summary {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 12px;
        margin-bottom: 28px;
      }}
      .card {{
        background: linear-gradient(145deg, #0c1223, #11182f);
        border-radius: 18px;
        padding: 18px;
        border: 1px solid rgba(148, 163, 184, 0.25);
        min-height: 100px;
      }}
      .label {{
        font-size: 0.8rem;
        color: #94a3b8;
        margin-bottom: 6px;
        text-transform: uppercase;
        letter-spacing: 0.1em;
      }}
      .value {{
        font-size: 1.8rem;
        font-weight: 600;
      }}
      .grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
        gap: 18px;
      }}
      table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 0.95rem;
      }}
      th {{
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #94a3b8;
        padding: 10px 6px;
      }}
      td {{
        padding: 6px 6px;
        border-top: 1px solid rgba(148, 163, 184, 0.25);
      }}
      .pill {{
        display: inline-flex;
        padding: 6px 12px;
        border-radius: 999px;
        background: rgba(59, 130, 246, 0.2);
        color: #bfdbfe;
        margin: 4px 6px 4px 0;
        font-size: 0.85rem;
      }}
      .charts {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 20px;
        margin: 20px 0 32px;
      }}
    </style>
  </head>
  <body>
    <main>
      <h1>Expanded Financial Dashboard</h1>
      <p>Generated from <code>Income.xlsx</code>. Refresh every time the workbook changes.</p>

      <section class="summary">
        <article class="card">
          <div class="label">Bank Balances</div>
          <div class="value">₹{data['totals']['bank_balance']:,.0f}</div>
        </article>
        <article class="card">
          <div class="label">Fixed Deposits</div>
          <div class="value">₹{data['totals']['fixed_deposits']:,.0f}</div>
        </article>
        <article class="card">
          <div class="label">Stocks</div>
          <div class="value">₹{data['totals']['stocks']:,.0f}</div>
        </article>
        <article class="card">
          <div class="label">Mutual Funds</div>
          <div class="value">₹{data['totals']['mutual_funds']:,.0f}</div>
        </article>
        <article class="card">
          <div class="label">Chits</div>
          <div class="value">₹{data['totals']['chits']:,.0f}</div>
        </article>
        <article class="card">
          <div class="label">Loan Out / Liability</div>
          <div class="value">₹{data['totals']['loan_out']:,.0f} / ₹{abs(data['totals']['loan_liability']):,.0f}</div>
        </article>
        <article class="card">
          <div class="label">Computed Net Worth</div>
          <div class="value">₹{data['totals']['net_worth']:,.0f}</div>
        </article>
      </section>

      <section class="charts">
        <article class="card">
          <h2>Asset Composition</h2>
          <canvas id="assetChart"></canvas>
        </article>
        <article class="card">
          <h2>Spending vs Earnings</h2>
          <canvas id="spendingChart"></canvas>
        </article>
      </section>

      <section class="card">
        <h2>Earnings Breakdown</h2>
        <div>
          {"".join(f'<span class="pill">{item["label"]}: ₹{item["amount"]:,.0f}</span>' for item in data["earnings"])}
        </div>
      </section>

      <section>
        <h2>Banks</h2>
        <article class="card">
          <table>
            <thead>
              <tr><th>Bank</th><th>Purpose</th><th>Balance</th><th>User ID</th></tr>
            </thead>
            <tbody>
              {render_rows(data["banks"], ["name", "purpose", "balance", "user_id"])}
            </tbody>
          </table>
        </article>
      </section>

      <section>
        <h2>Fixed Deposits</h2>
        <article class="card">
          <table>
            <thead>
              <tr><th>Account</th><th>Invested</th><th>Current</th><th>Days to Mature</th></tr>
            </thead>
            <tbody>
              {render_rows(data["fixed_deposits"], ["account_id", "Invested", "Current Amount", "Days To Mature"])}
            </tbody>
          </table>
        </article>
      </section>

      <section class="grid" style="margin-top: 24px;">
        <article class="card">
          <h2>Stocks</h2>
          <table>
            <thead>
              <tr><th>Symbol</th><th>Exchange</th><th>Invested</th><th>Current</th><th>Source</th></tr>
            </thead>
            <tbody>
              {render_rows(data["stocks"], ["Symbol", "Exchange", "Invested", "current", "Source"])}
            </tbody>
          </table>
        </article>
        <article class="card">
          <h2>Mutual Funds</h2>
          <table>
            <thead>
              <tr><th>ID</th><th>Invested</th><th>Current</th></tr>
            </thead>
            <tbody>
              {render_rows(data["mutual_funds"], ["id", "Invested", "Current"])}
            </tbody>
          </table>
        </article>
      </section>

      <section class="grid" style="margin-top: 24px;">
        <article class="card">
          <h2>Standard Chits</h2>
          <table>
            <thead>
              <tr><th>Org</th><th>Current Value</th><th>Notes</th></tr>
            </thead>
            <tbody>
              {render_rows(data["standard_chits"], ["Organsation", "Current_value", "Unnamed: 9"])}
            </tbody>
          </table>
        </article>
        <article class="card">
          <h2>Variable Chits</h2>
          <table>
            <thead>
              <tr><th>Name</th><th>Net Value</th><th>EMI Paid</th></tr>
            </thead>
            <tbody>
              {render_rows(data["variable_chits"], ["Name", "net_value", "emi_paid"])}
            </tbody>
          </table>
        </article>
      </section>

      <section class="grid" style="margin-top: 28px;">
        <article class="card">
          <h2>Spendings</h2>
          <table>
            <thead>
              <tr><th>Type</th><th>Amount</th><th>Person</th><th>Recipient</th></tr>
            </thead>
            <tbody>
              {render_rows(data["spending_rows"], ["Spending Type", "Amount", "Person", "Recipient"])}
            </tbody>
          </table>
        </article>
        <article class="card">
          <h2>Utilities</h2>
          <table>
            <thead>
              <tr><th>Type</th><th>Amount</th></tr>
            </thead>
            <tbody>
              {render_rows(data["utility_rows"], ["Type", "Amount"])}
            </tbody>
          </table>
        </article>
      </section>

      <section style="margin-top: 28px;">
        <article class="card">
          <h2>Overall</h2>
          <table>
            <thead>
              <tr><th>Label</th><th>Amount</th></tr>
            </thead>
            <tbody>
              {render_rows(data["overall_rows"], ["label", "amount"])}
            </tbody>
          </table>
        </article>
      </section>
    </main>
    <script>
      const assetChart = new Chart(document.getElementById("assetChart"), {{
        type: "doughnut",
        data: {{
          labels: {json.dumps(asset_labels)},
          datasets: [{{
            data: {json.dumps(asset_values)},
            backgroundColor: ["#38bdf8", "#22d3ee", "#a78bfa", "#f472b6", "#34d399"],
          }}],
        }},
        options: {{
          plugins: {{
            tooltip: {{
              callbacks: {{
                label: (context) => {{
                  const value = Number(context.parsed).toLocaleString();
                  return `${{context.label}}: ₹${{value}}`;
                }},
              }},
            }},
          }},
        }},
      }});

      const spendingChart = new Chart(document.getElementById("spendingChart"), {{
        type: "bar",
        data: {{
          labels: {json.dumps(spending_labels)},
          datasets: [{{
            label: "Flow",
            data: {json.dumps(spending_values)},
            backgroundColor: "#38bdf8",
          }}],
        }},
        options: {{
          scales: {{
            y: {{
              ticks: {{
                callback: (value) => `₹${{value.toLocaleString()}}`,
              }},
            }},
          }},
        }},
      }});
    </script>
  </body>
</html>
"""
    output_path = Path(output)
    output_path.write_text(html_content, encoding="utf-8")
    print(f"Dashboard HTML written to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Build an expanded finance dashboard")
    parser.add_argument(
        "--source",
        "-s",
        type=Path,
        default=Path.home() / "Desktop" / "Income" / "income" / "Income.xlsx",
        help="Path to Income.xlsx",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("dashboard.html"),
        help="Output HTML path",
    )

    args = parser.parse_args()
    data = build_dashboard_data(args.source)
    render_dashboard(data, args.output)


if __name__ == "__main__":
    main()
