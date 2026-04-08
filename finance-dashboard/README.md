# Finance Dashboard

This helper reads the supplied `Income.xlsx` workbook, summarizes the key holdings/incomes/expenses, and generates a self-contained HTML dashboard (`dashboard.html`) that you can open in any browser.

## Requirements
- Python 3.9+ (tested with 3.14)
- `pandas`
- `openpyxl`

Install dependencies with:
```
pip install pandas openpyxl
```

## Usage
```
python finance-dashboard/build_dashboard.py --source "C:\Users\venka\Desktop\Income\income\Income.xlsx" --output finance-dashboard/dashboard.html
```

If you omit `--source`, the script defaults to the path above. If you omit `--output`, it writes `dashboard.html` alongside the script.

## Dashboard highlights
- Responsive summary cards for banks, fixed deposits, stocks, mutual funds, chits, and loans so you can quickly spot the biggest buckets.
- Asset composition doughnut plus spending-vs-earnings bar chart to visualize allocation and cash flow.
- Detailed sections/tables for banks, fixed deposits, stocks, mutual funds, chits (standard + variable), spendings, utilities, earnings pills, and an overall line-item table.
- Everything renders into one standalone HTML file that you can email, host as static content, or keep as a local snapshot.

Re-run the script whenever the Excel file changes to refresh the dashboard.
