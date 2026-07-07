from pydantic import BaseModel

class ShipmentCreate(BaseModel):
    product_id: int
    quantity: int
    origin: str
    destination: str

class Shipment(BaseModel):
    id: int
    product_id: int
    quantity: int
    origin: str
    destination: str

class ProductCreate(BaseModel):
    name: str

class Product(BaseModel):
    id: int
    name: str

class ImportRequest(BaseModel):
    file_name: str