from fastapi import FastAPI
from database import get_connection, init_db
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from Datas import Data
from models import (
    Product,
    Shipment,
    ShipmentCreate,
    ProductCreate,
    ImportRequest
)
import pandas as pd
import io
import glob
from datetime import datetime
from pathlib import Path
import config

app= FastAPI()

@app.on_event("startup")
def on_startup():
    # Ensure product/shipment tables exist, whether the DB file is fresh,
    # empty, or already populated. Runs every time the app boots (including
    # on Render), not just under pytest.
    init_db()

@app.get("/")
def home():
    return {"message": "Welcome to my Shipment API"}

@app.get(
    "/shipments",
    response_model=list[Shipment]
)
def get_shipments(limit: int = 5):
    conn= get_connection()

    cursor= conn.execute("""
        SELECT * FROM shipment LIMIT ?
    """, (limit,)
    )

    shipments= [dict(row) for row in cursor.fetchall()]
    conn.close()

    return shipments

def _stream_csv(df: pd.DataFrame, filename_prefix: str) -> StreamingResponse:
    """Shared helper: turn a DataFrame into a downloadable CSV response."""
    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    buffer.seek(0)

    filename = datetime.now().strftime(f"{filename_prefix}_%Y%m%d_%H%M%S.csv")

    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.get("/export/shipments")
def export_shipments():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM shipment", conn)
    conn.close()

    return _stream_csv(df, "shipments")

@app.get("/export/products")
def export_products():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM product", conn)
    conn.close()

    return _stream_csv(df, "products")

@app.get("/export")
def export_shipments_alias():
    # Kept for backwards compatibility with anything already linking to
    # the old /export path; behaves the same as /export/shipments.
    return export_shipments()

@app.get(
    "/shipments/{index}",
    response_model=Shipment
)
def get_shipment(index: int):
    conn= get_connection()
    cursor= conn.execute("""
        SELECT * FROM shipment WHERE id= ?
    """, (index,)
    )

    shipment= cursor.fetchone()

    conn.close()

    if shipment:
        return dict(shipment)
    
    raise HTTPException(
        status_code=404,
        detail="Shipment not found"
    )

@app.post("/shipments")
def create_shipment(shipment: ShipmentCreate):

    conn = get_connection()

    # Check if product exists
    cursor = conn.execute(
        """
        SELECT id
        FROM product
        WHERE id = ?
        """,
        (shipment.product_id,)
    )

    product = cursor.fetchone()

    if product is None:
        conn.close()
        raise HTTPException(
            status_code=404,
            detail="Product not found."
        )

    cursor = conn.execute(
        """
        INSERT INTO shipment
        (product_id, quantity, origin, destination)

        VALUES (?, ?, ?, ?)
        """,
        (
            shipment.product_id,
            shipment.quantity,
            shipment.origin,
            shipment.destination
        )
    )

    conn.commit()

    shipment_id = cursor.lastrowid

    conn.close()

    return {
        "message": "Shipment successfully created",
        "shipment_id": shipment_id
    }
        
@app.get(
    "/products",
    response_model=list[Product]
)
def get_products():

    conn = get_connection()

    cursor = conn.execute(
        "SELECT * FROM product"
    )

    products = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return products


@app.post("/products")
def create_product(product: ProductCreate):

    conn = get_connection()

    cursor = conn.execute(
        """
        SELECT id
        FROM product
        WHERE name = ?
        """,
        (product.name,)
    )

    existing = cursor.fetchone()

    if existing:
        conn.close()

        raise HTTPException(
            status_code=409,
            detail="Product already exists."
        )

    cursor = conn.execute(
        """
        INSERT INTO product(name)
        VALUES(?)
        """,
        (product.name,)
    )

    conn.commit()

    new_id = cursor.lastrowid

    conn.close()

    return {
        "message":"Product added",
        "product_id":new_id
    }

@app.post("/import")
def import_all(file_name: str):
    csv_path = config.DATA_FOLDER / file_name

    if "*" in file_name:
        # Path.exists() can't check a wildcard pattern literally, so use
        # glob to see whether it matches at least one real file.
        matches = glob.glob(str(csv_path))
        if not matches:
            return {"message": "CSV file not found."}
    else:
        if not csv_path.exists():
            return {"message": "CSV file not found."}

    d = Data()
    d.run(str(csv_path), str(config.DATABASE))

    return {"message": "Import completed"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
