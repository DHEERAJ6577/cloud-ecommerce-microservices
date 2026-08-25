from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import update

import models
import schemas
from database import engine, get_db

app = FastAPI(
    title="Product Service",
    description="Product management microservice",
    version="1.0.0"
)

# Create database tables
models.Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    return {
        "service": "product-service",
        "status": "running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.post("/products", response_model=schemas.ProductResponse)
def create_product(
    product: schemas.ProductCreate,
    db: Session = Depends(get_db)
):
    new_product = models.Product(
        name=product.name,
        description=product.description,
        price=product.price,
        stock=product.stock
    )

    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    return new_product


@app.get("/products", response_model=list[schemas.ProductResponse])
def get_products(db: Session = Depends(get_db)):
    return db.query(models.Product).all()


@app.get("/products/{product_id}", response_model=schemas.ProductResponse)
def get_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    product = db.query(models.Product).filter(
        models.Product.id == product_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    return product


@app.put("/products/{product_id}", response_model=schemas.ProductResponse)
def update_product(
    product_id: int,
    product_data: schemas.ProductCreate,
    db: Session = Depends(get_db)
):
    product = db.query(models.Product).filter(
        models.Product.id == product_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    product.name = product_data.name
    product.description = product_data.description
    product.price = product_data.price
    product.stock = product_data.stock

    db.commit()
    db.refresh(product)

    return product


@app.delete("/products/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    product = db.query(models.Product).filter(
        models.Product.id == product_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    db.delete(product)
    db.commit()

    return {
        "message": "Product deleted successfully"
    }
# DECREASE STOCK
@app.post(
    "/products/{product_id}/decrease-stock",
    response_model=schemas.ProductResponse
)
def decrease_stock(
    product_id: int,
    stock_data: schemas.StockDecreaseRequest,
    db: Session = Depends(get_db)
):
    if stock_data.quantity <= 0:
        raise HTTPException(
            status_code=400,
            detail="Quantity must be greater than zero"
        )

    result = db.execute(
        update(models.Product)
        .where(
            models.Product.id == product_id,
            models.Product.stock >= stock_data.quantity
        )
        .values(
            stock=models.Product.stock - stock_data.quantity
        )
    )

    if result.rowcount == 0:
        product = db.query(models.Product).filter(
            models.Product.id == product_id
        ).first()

        if not product:
            raise HTTPException(
                status_code=404,
                detail="Product not found"
            )

        raise HTTPException(
            status_code=400,
            detail="Insufficient stock"
        )

    db.commit()

    product = db.query(models.Product).filter(
        models.Product.id == product_id
    ).first()

    return product

# INCREASE STOCK
@app.post(
    "/products/{product_id}/increase-stock",
    response_model=schemas.ProductResponse
)
def increase_stock(
    product_id: int,
    stock_data: schemas.StockIncreaseRequest,
    db: Session = Depends(get_db)
):
    if stock_data.quantity <= 0:
        raise HTTPException(
            status_code=400,
            detail="Quantity must be greater than zero"
        )

    product = (
        db.query(models.Product)
        .filter(models.Product.id == product_id)
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    product.stock += stock_data.quantity

    db.commit()
    db.refresh(product)

    return product