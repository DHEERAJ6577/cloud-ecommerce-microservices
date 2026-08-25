from fastapi import FastAPI, Depends, Header, HTTPException
from sqlalchemy.orm import Session
import httpx

import models
import schemas

from database import engine, Base, get_db


# Create database tables
Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Order Service",
    description="Order management microservice",
    version="1.0.0"
)


PRODUCT_SERVICE_URL = "http://product-service:8001"


# =========================
# GENERAL ROUTES
# =========================

@app.get("/")
def root():
    return {
        "service": "order-service",
        "status": "running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


# =========================
# CREATE ORDER
# =========================

@app.post("/orders", response_model=schemas.OrderResponse)
async def create_order(
    order_data: schemas.OrderCreate,
    x_user_id: int = Header(...),
    db: Session = Depends(get_db)
):
    if x_user_id <= 0:
        raise HTTPException(
            status_code=400,
            detail="Invalid user ID"
        )

    product_details = []
    total_amount = 0.0

    # ---------------------------------
    # 1. Validate ALL products first
    # ---------------------------------

    async with httpx.AsyncClient() as client:

        for item in order_data.items:

            response = await client.get(
                f"{PRODUCT_SERVICE_URL}/products/{item.product_id}"
            )

            if response.status_code == 404:
                raise HTTPException(
                    status_code=404,
                    detail=f"Product {item.product_id} not found"
                )

            if response.status_code >= 400:
                raise HTTPException(
                    status_code=502,
                    detail="Product Service error"
                )

            product = response.json()

            if product["stock"] < item.quantity:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient stock for product {item.product_id}"
                )

            price = float(product["price"])
            item_total = price * item.quantity

            total_amount += item_total

            product_details.append({
                "product_id": item.product_id,
                "quantity": item.quantity,
                "price": price
            })

        # ---------------------------------
        # 2. Decrease stock
        # ---------------------------------

        decreased_items = []

        try:

            for item in product_details:

                response = await client.post(
                    f"{PRODUCT_SERVICE_URL}/products/{item['product_id']}/decrease-stock",
                    json={
                        "quantity": item["quantity"]
                    }
                )

                if response.status_code >= 400:

                    # Restore anything already decreased
                    for decreased in decreased_items:

                        await client.post(
                            f"{PRODUCT_SERVICE_URL}/products/{decreased['product_id']}/increase-stock",
                            json={
                                "quantity": decreased["quantity"]
                            }
                        )

                    raise HTTPException(
                        status_code=400,
                        detail=(
                            f"Unable to decrease stock for "
                            f"product {item['product_id']}"
                        )
                    )

                decreased_items.append(item)

            # ---------------------------------
            # 3. Create order in database
            # ---------------------------------

            try:

                new_order = models.Order(
                    user_id=x_user_id,
                    total_amount=total_amount,
                    status="pending"
                )

                db.add(new_order)
                db.flush()

                # ---------------------------------
                # 4. Create order items
                # ---------------------------------

                for item in product_details:

                    order_item = models.OrderItem(
                        order_id=new_order.id,
                        product_id=item["product_id"],
                        quantity=item["quantity"],
                        price=item["price"]
                    )

                    db.add(order_item)

                db.commit()
                db.refresh(new_order)

                return new_order

            except Exception:

                db.rollback()

                # ---------------------------------
                # 5. Compensating action
                # ---------------------------------

                for item in decreased_items:

                    await client.post(
                        f"{PRODUCT_SERVICE_URL}/products/{item['product_id']}/increase-stock",
                        json={
                            "quantity": item["quantity"]
                        }
                    )

                raise HTTPException(
                    status_code=500,
                    detail="Order creation failed; stock was restored"
                )

        except HTTPException:
            raise

        except Exception:

            for item in decreased_items:

                try:
                    await client.post(
                        f"{PRODUCT_SERVICE_URL}/products/{item['product_id']}/increase-stock",
                        json={
                            "quantity": item["quantity"]
                        }
                    )
                except Exception:
                    pass

            raise HTTPException(
                status_code=502,
                detail="Inventory update failed"
            )


# =========================
# GET MY ORDERS
# =========================

@app.get(
    "/orders",
    response_model=list[schemas.OrderResponse]
)
def get_orders(
    x_user_id: int = Header(...),
    db: Session = Depends(get_db)
):
    if x_user_id <= 0:
        raise HTTPException(
            status_code=400,
            detail="Invalid user ID"
        )

    orders = (
        db.query(models.Order)
        .filter(models.Order.user_id == x_user_id)
        .order_by(models.Order.id.desc())
        .all()
    )

    return orders


# =========================
# GET ONE MY ORDER
# =========================

@app.get(
    "/orders/{order_id}",
    response_model=schemas.OrderResponse
)
def get_order(
    order_id: int,
    x_user_id: int = Header(...),
    db: Session = Depends(get_db)
):
    if x_user_id <= 0:
        raise HTTPException(
            status_code=400,
            detail="Invalid user ID"
        )

    order = (
        db.query(models.Order)
        .filter(
            models.Order.id == order_id,
            models.Order.user_id == x_user_id
        )
        .first()
    )

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    return order

# =========================
# CANCEL ORDER
# =========================

@app.post(
    "/orders/{order_id}/cancel",
    response_model=schemas.OrderResponse
)
async def cancel_order(
    order_id: int,
    x_user_id: int = Header(...),
    db: Session = Depends(get_db)
):
    if x_user_id <= 0:
        raise HTTPException(
            status_code=400,
            detail="Invalid user ID"
        )

    order = (
        db.query(models.Order)
        .filter(
            models.Order.id == order_id,
            models.Order.user_id == x_user_id
        )
        .first()
    )

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    if order.status == "cancelled":
        raise HTTPException(
            status_code=400,
            detail="Order is already cancelled"
        )

    if order.status != "pending":
        raise HTTPException(
            status_code=400,
            detail="Only pending orders can be cancelled"
        )

    async with httpx.AsyncClient() as client:

        restored_items = []

        try:
            for item in order.items:

                response = await client.post(
                    f"{PRODUCT_SERVICE_URL}/products/{item.product_id}/increase-stock",
                    json={
                        "quantity": item.quantity
                    }
                )

                if response.status_code >= 400:
                    raise HTTPException(
                        status_code=502,
                        detail=(
                            f"Unable to restore stock "
                            f"for product {item.product_id}"
                        )
                    )

                restored_items.append(item)

            order.status = "cancelled"

            db.commit()
            db.refresh(order)

            return order

        except HTTPException:
            db.rollback()

            # If some products were already restored,
            # decrease them again to compensate.
            for item in restored_items:
                try:
                    await client.post(
                        f"{PRODUCT_SERVICE_URL}/products/{item.product_id}/decrease-stock",
                        json={
                            "quantity": item.quantity
                        }
                    )
                except Exception:
                    pass

            raise

        except Exception:
            db.rollback()

            for item in restored_items:
                try:
                    await client.post(
                        f"{PRODUCT_SERVICE_URL}/products/{item.product_id}/decrease-stock",
                        json={
                            "quantity": item.quantity
                        }
                    )
                except Exception:
                    pass

            raise HTTPException(
                status_code=500,
                detail="Order cancellation failed"
            )

# =========================
# UPDATE ORDER STATUS
# =========================

@app.put(
    "/orders/{order_id}/status",
    response_model=schemas.OrderResponse
)
def update_order_status(
    order_id: int,
    status_data: schemas.OrderStatusUpdate,
    x_user_id: int = Header(...),
    db: Session = Depends(get_db)
):
    if x_user_id <= 0:
        raise HTTPException(
            status_code=400,
            detail="Invalid user ID"
        )

    order = (
        db.query(models.Order)
        .filter(models.Order.id == order_id)
        .first()
    )

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    new_status = status_data.status.lower()

    allowed_statuses = {
        "pending",
        "confirmed",
        "completed",
        "cancelled"
    }

    if new_status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail="Invalid order status"
        )

    current_status = order.status

    valid_transitions = {
        "pending": {"confirmed", "cancelled"},
        "confirmed": {"completed"},
        "completed": set(),
        "cancelled": set()
    }

    if new_status not in valid_transitions.get(current_status, set()):
        raise HTTPException(
            status_code=400,
            detail=(
                f"Cannot change order status "
                f"from {current_status} to {new_status}"
            )
        )

    order.status = new_status

    db.commit()
    db.refresh(order)

    return order