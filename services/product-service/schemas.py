from pydantic import BaseModel, ConfigDict


class ProductCreate(BaseModel):
    name: str
    description: str | None = None
    price: float
    stock: int


class ProductResponse(BaseModel):
    id: int
    name: str
    description: str | None
    price: float
    stock: int

    model_config = ConfigDict(from_attributes=True)


class StockDecreaseRequest(BaseModel):
    quantity: int

class StockIncreaseRequest(BaseModel):
    quantity: int