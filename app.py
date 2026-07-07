from fastapi import FastAPI
from database import get_connection
from fastapi import HTTPException
from Datas import Data
from models import (
    Product,
    Shipment,
    ShipmentCreate,
    ProductCreate,
    ImportRequest
)
import pandas as pd
from datetime import datetime
from pathlib import Path
import config

app= FastAPI()

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

@app.get("/export")
def export_shipments():

    conn = get_connection()
    df = pd.read_sql("SELECT * FROM shipment", conn)
    conn.close()

    filename = config.EXPORT_FOLDER / datetime.now().strftime("shipments_%Y%m%d_%H%M%S.csv")
    df.to_csv(filename, index=False)

    return {"message": "CSV exported successfully.", "location": str(filename)}

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

    if not csv_path.exists():
        return {"message": "CSV file not found."}

    d = Data()
    d.run(str(csv_path), str(config.DATABASE))

    return {"message": "Import completed"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
