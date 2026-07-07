# Shipment API

A small [FastAPI](https://fastapi.tiangolo.com/) service for tracking products and shipments, backed by SQLite. It also includes a CSV import pipeline that can load and reconcile shipment data spread across multiple raw source files.

## Features

- **Shipments & Products API** — create and list products and shipments, fetch a single shipment by ID
- **CSV import** — load shipment data from CSV files into the database, either from a single self-contained file or from multiple related files that need to be joined
- **CSV export** — dump the current `shipment` table to a timestamped CSV file
- **Test suite** — pytest coverage for the API endpoints, the database layer, and the CSV import logic

## Tech stack

- [FastAPI](https://fastapi.tiangolo.com/) + [Pydantic](https://docs.pydantic.dev/) for the API and data validation
- [SQLite](https://www.sqlite.org/) for storage
- [pandas](https://pandas.pydata.org/) for CSV handling and SQL data wrangling
- [pytest](https://docs.pytest.org/) for testing

## Project structure

```
.
├── app.py                 # FastAPI routes
├── models.py               # Pydantic request/response models
├── database.py              # SQLite connection helper
├── config.py                # Paths for the DB, data folder, and exports
├── Datas.py                 # CSV import/reconciliation logic
├── requirements.txt
├── shipping_data_0.csv       # Self-contained sample shipment data
├── shipping_data_1.csv       # Product-per-shipment rows (needs joining)
├── shipping_data_2.csv       # Origin/destination per shipment (needs joining)
├── conftest.py               # Shared pytest fixtures (test DB, test client)
├── test_home.py
├── test_products.py
├── test_shipments.py
├── test_import_export.py
├── test_database.py
└── test_datas.py
```

## Getting started

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the API

```bash
python app.py
```

The API will be available at `http://127.0.0.1:8000`. Interactive docs (Swagger UI) are at `http://127.0.0.1:8000/docs`.

## API Endpoints

| Method | Path                | Description                              |
|--------|---------------------|-------------------------------------------|
| GET    | `/`                  | Health check / welcome message            |
| GET    | `/products`          | List all products                         |
| POST   | `/products`          | Create a new product                      |
| GET    | `/shipments`         | List shipments (supports `?limit=`)       |
| GET    | `/shipments/{id}`    | Get a single shipment by ID                |
| POST   | `/shipments`         | Create a new shipment                      |
| POST   | `/import`            | Import a CSV file from the data folder     |
| GET    | `/export`            | Export the shipment table to a CSV file    |

### Example: create a product

```bash
curl -X POST http://127.0.0.1:8000/products \
  -H "Content-Type: application/json" \
  -d '{"name": "Laptop"}'
```

### Example: create a shipment

```bash
curl -X POST http://127.0.0.1:8000/shipments \
  -H "Content-Type: application/json" \
  -d '{"product_id": 1, "quantity": 50, "origin": "Warehouse A", "destination": "Store B"}'
```

## CSV import

Shipment data can come in two shapes:

- **Single-file format** (like `shipping_data_0.csv`): one row per shipment, with `origin_warehouse`, `destination_store`, `product`, and `product_quantity` columns.
- **Multi-file format** (`shipping_data_1.csv` + `shipping_data_2.csv`): split across files and joined on `shipment_identifier` — one file has one row per product per shipment (quantity = row count), the other has the origin/destination for each shipment.

The `/import` endpoint (and the `Data` class in `Datas.py`) detects which case applies and reconciles the data before inserting it into the `shipment` and `product` tables, creating any new products it encounters along the way.

## Running tests

```bash
pytest
```

Tests run against an isolated SQLite database (`tests/test_database.db`) created fresh via fixtures in `conftest.py`, so they won't touch your real data.

## Configuration

Paths for the database, data folder, and export folder are defined in `config.py` and created automatically on first run:

```python
DATABASE = BASE_DIR / "shipment_database.db"
DATA_FOLDER = BASE_DIR / "data" / "source"
EXPORT_FOLDER = BASE_DIR / "exports"
```
