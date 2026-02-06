# AI Sales (Local Sales Management)

A local, offline-friendly sales and monitoring console for small teams. It uses SQLite for durable storage, supports product and customer management, captures rich purchase details, and generates daily reports.

## Highlights

- Full local storage (SQLite) with last-N purchase retention
- Product and customer management (add/edit/search)
- Detailed purchase capture (quantity, tax, discounts, payment, channel, region, etc.)
- Daily sales report with 7-day trend and top products
- CSV export and database backup
- Rotating logs and config validation
- Optional AI summary (only if you configure an LLM)

## Quick Start (Windows)

1. Open VS Code.
2. Open the folder `Ai Agent`.
3. Open a terminal.

Create and activate a virtual environment:

```bash
python -m venv venv
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the app:

```bash
python main.py
```

## Configuration (.env)

Required:
- `COMPANY_NAME`
- `COMPANY_EMAIL`
- `ALERT_EMAIL`

Defaults:
- `DEFAULT_CURRENCY` (e.g., USD)
- `DEFAULT_TAX_RATE` (0 to 1)
- `DEFAULT_PAYMENT_STATUS`
- `DEFAULT_PAYMENT_TERMS`
- `DEFAULT_FULFILLMENT_STATUS`
- `DEFAULT_CHANNEL`
- `DEFAULT_SOURCE`
- `DEFAULT_REGION`
- `DEFAULT_SALES_REP`

Operational:
- `MAX_RECENT_PURCHASES`
- `LOG_LEVEL`
- `DB_TIMEOUT`

Optional AI (only if you want summaries from a provider):
- `LLM_PROVIDER=openai_compatible`
- `API_KEY=your_api_key_here`
- `LLM_ENDPOINT=your-provider-endpoint`
- `LLM_MODEL=your-model-name`

Tip: Use `.env.example` as a template.

## Menu Overview

1. Add a sale
2. View last purchases
3. Search purchases
4. Daily sales report
5. Export purchases to CSV
6. Backup database
7. Manage products
8. Manage customers
9. Exit

## Data Model (SQLite)

Tables:
- `products`: name, sku, category, price, cost, tax_rate, unit, description, features, best_for, active
- `customers`: name, email, phone, company, industry, segment, status, lead_source, address, notes
- `purchases`: quantity, unit_price, discounts, tax, total, currency, payment terms, payment/fulfillment status, channel, region, invoice id, tags, notes

CSV files in `data/` are only used for initial seeding.

## Export & Backup

- Exports go to `data/exports/`
- Backups go to `data/backups/`

## Git (Initialize + Push)

```bash
git init
git add .
git commit -m "Initial commit"
```

Then add your remote and push:

```bash
git remote add origin <YOUR_GIT_URL>
git branch -M main
git push -u origin main
```

## Files

- `main.py` entry point
- `monitoring.py` reporting and alerts
- `db.py` SQLite storage layer
- `ui.py` table formatting
- `logger.py` logging
- `config.py` configuration + data setup
- `llm_client.py` optional AI client

## Notes

This is a local, offline-first tool. It does not send data anywhere unless you explicitly configure an LLM endpoint.

## License

MIT License. See `LICENSE`.
