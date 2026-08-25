from fastapi import FastAPI, Depends, Header, HTTPException
from sqlalchemy.orm import Session
import httpx

import models
import schemas

from database import engine, Base, get_db


# Create database tables
Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Cart Service",
    description="Shopping cart microservice",
    version="1.0.0"
)


PRODUCT_SERVICE_URL = "http://product-service:8001"
ORDER_SERVICE_URL = "http://order-service:8002"


# =========================
# GENERAL ROUTES
# =========================

@app.get("/")
def root():
    return {
        "service": "cart-service",
        "status": "running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


# =========================
# ADD ITEM TO CART
# =========================

@app.post(
    "/cart/items",
    response_model=schemas.CartItemResponse
)
async def add_to_cart(
    item_data: schemas.CartItemCreate,
    x_user_id: int = Header(...),
    db: Session = Depends(get_db)
):
    if x_user_id <= 0:
        raise HTTPException(
            status_code=400,
            detail="Invalid user ID"
        )

    # Check that the product exists and get current stock
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{PRODUCT_SERVICE_URL}/products/{item_data.product_id}"
        )

    if response.status_code == 404:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    if response.status_code >= 400:
        raise HTTPException(
            status_code=502,
            detail="Product Service error"
        )

    product = response.json()

    # Check available stock
    if product["stock"] < item_data.quantity:
        raise HTTPException(
            status_code=400,
            detail="Insufficient stock"
        )

    # Check whether this product is already in the user's cart
    existing_item = (
        db.query(models.CartItem)
        .filter(
            models.CartItem.user_id == x_user_id,
            models.CartItem.product_id == item_data.product_id
        )
        .first()
    )

    if existing_item:
        new_quantity = existing_item.quantity + item_data.quantity

        if product["stock"] < new_quantity:
            raise HTTPException(
                status_code=400,
                detail="Insufficient stock for requested cart quantity"
            )

        existing_item.quantity = new_quantity

        db.commit()
        db.refresh(existing_item)

        return existing_item

    # Create new cart item
    new_item = models.CartItem(
        user_id=x_user_id,
        product_id=item_data.product_id,
        quantity=item_data.quantity
    )

    db.add(new_item)
    db.commit()
    db.refresh(new_item)

    return new_item


# =========================
# GET MY CART
# =========================

@app.get(
    "/cart",
    response_model=list[schemas.CartItemResponse]
)
def get_cart(
    x_user_id: int = Header(...),
    db: Session = Depends(get_db)
):
    if x_user_id <= 0:
        raise HTTPException(
            status_code=400,
            detail="Invalid user ID"
        )

    return (
        db.query(models.CartItem)
        .filter(models.CartItem.user_id == x_user_id)
        .order_by(models.CartItem.id)
        .all()
    )


# =========================
# UPDATE CART ITEM
# =========================

@app.put(
    "/cart/items/{product_id}",
    response_model=schemas.CartItemResponse
)
async def update_cart_item(
    product_id: int,
    item_data: schemas.CartItemUpdate,
    x_user_id: int = Header(...),
    db: Session = Depends(get_db)
):
    if x_user_id <= 0:
        raise HTTPException(
            status_code=400,
            detail="Invalid user ID"
        )

    item = (
        db.query(models.CartItem)
        .filter(
            models.CartItem.user_id == x_user_id,
            models.CartItem.product_id == product_id
        )
        .first()
    )

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Cart item not found"
        )

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{PRODUCT_SERVICE_URL}/products/{product_id}"
        )

    if response.status_code == 404:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    if response.status_code >= 400:
        raise HTTPException(
            status_code=502,
            detail="Product Service error"
        )

    product = response.json()

    if product["stock"] < item_data.quantity:
        raise HTTPException(
            status_code=400,
            detail="Insufficient stock"
        )

    item.quantity = item_data.quantity

    db.commit()
    db.refresh(item)

    return item


# =========================
# REMOVE CART ITEM
# =========================

@app.delete("/cart/items/{product_id}")
def remove_from_cart(
    product_id: int,
    x_user_id: int = Header(...),
    db: Session = Depends(get_db)
):
    if x_user_id <= 0:
        raise HTTPException(
            status_code=400,
            detail="Invalid user ID"
        )

    item = (
        db.query(models.CartItem)
        .filter(
            models.CartItem.user_id == x_user_id,
            models.CartItem.product_id == product_id
        )
        .first()
    )

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Cart item not found"
        )

    db.delete(item)
    db.commit()

    return {
        "message": "Item removed from cart"
    }


# =========================
# CLEAR CART
# =========================

@app.delete("/cart")
def clear_cart(
    x_user_id: int = Header(...),
    db: Session = Depends(get_db)
):
    if x_user_id <= 0:
        raise HTTPException(
            status_code=400,
            detail="Invalid user ID"
        )

    (
        db.query(models.CartItem)
        .filter(models.CartItem.user_id == x_user_id)
        .delete(synchronize_session=False)
    )

    db.commit()

    return {
        "message": "Cart cleared successfully"
    }


# =========================
# CHECKOUT
# =========================

@app.post("/checkout")
async def checkout(
    x_user_id: int = Header(...),
    db: Session = Depends(get_db)
):
    if x_user_id <= 0:
        raise HTTPException(
            status_code=400,
            detail="Invalid user ID"
        )

    # Get current user's cart
    cart_items = (
        db.query(models.CartItem)
        .filter(models.CartItem.user_id == x_user_id)
        .order_by(models.CartItem.id)
        .all()
    )

    if not cart_items:
        raise HTTPException(
            status_code=400,
            detail="Cart is empty"
        )

    # Convert cart to order items
    order_items = [
        {
            "product_id": item.product_id,
            "quantity": item.quantity
        }
        for item in cart_items
    ]

    # Ask Order Service to create the order
    async with httpx.AsyncClient() as client:

        response = await client.post(
            f"{ORDER_SERVICE_URL}/orders",
            json={
                "items": order_items
            },
            headers={
                "X-User-ID": str(x_user_id)
            }
        )

    # If order creation fails, keep the cart
    if response.status_code >= 400:
        try:
            error = response.json()

            if isinstance(error, dict) and "detail" in error:
                detail = error["detail"]
            else:
                detail = error

        except Exception:
            detail = response.text

        raise HTTPException(
            status_code=response.status_code,
            detail=detail
        )

    order = response.json()

    # Clear cart only after successful order creation
    (
        db.query(models.CartItem)
        .filter(models.CartItem.user_id == x_user_id)
        .delete(synchronize_session=False)
    )

    db.commit()

    return order