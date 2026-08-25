from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import httpx

from jwt_auth import verify_token


# =========================
# AUTHORIZATION
# =========================

def require_admin(current_user: dict = Depends(verify_token)):
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )

    return current_user


# =========================
# APPLICATION
# =========================

app = FastAPI(
    title="E-Commerce API Gateway"
)


# =========================
# SERVICE URLs
# =========================

USER_SERVICE_URL = "http://user-service:8000"
PRODUCT_SERVICE_URL = "http://product-service:8001"
ORDER_SERVICE_URL = "http://order-service:8002"
CART_SERVICE_URL = "http://cart-service:8003"


# =========================
# RESPONSE FORWARDING
# =========================

async def forward_response(response):

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

    return response.json()


# =========================
# REQUEST MODELS
# =========================

class UserRequest(BaseModel):
    name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class ProductRequest(BaseModel):
    name: str
    description: str | None = None
    price: float
    stock: int


class OrderItemRequest(BaseModel):
    product_id: int
    quantity: int


class OrderRequest(BaseModel):
    items: list[OrderItemRequest]

class CartItemUpdateRequest(BaseModel):
    quantity: int


# =========================
# GENERAL ROUTES
# =========================

@app.get("/")
def root():
    return {
        "service": "api-gateway",
        "status": "running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


# =========================
# USER ROUTES
# =========================

@app.get("/users")
async def get_users():

    async with httpx.AsyncClient() as client:

        response = await client.get(
            f"{USER_SERVICE_URL}/users"
        )

    return await forward_response(response)


@app.post("/login")
async def login(user: LoginRequest):

    async with httpx.AsyncClient() as client:

        response = await client.post(
            f"{USER_SERVICE_URL}/login",
            json=user.model_dump()
        )

    return await forward_response(response)


@app.post("/users")
async def create_user(user: UserRequest):

    async with httpx.AsyncClient() as client:

        response = await client.post(
            f"{USER_SERVICE_URL}/users",
            json=user.model_dump()
        )

    return await forward_response(response)


@app.put("/users/{user_id}")
async def update_user(
    user_id: int,
    user: UserRequest,
    current_user: dict = Depends(verify_token)
):

    if int(current_user["sub"]) != user_id:

        raise HTTPException(
            status_code=403,
            detail="You can only modify your own account"
        )

    async with httpx.AsyncClient() as client:

        response = await client.put(
            f"{USER_SERVICE_URL}/users/{user_id}",
            json=user.model_dump()
        )

    return await forward_response(response)


@app.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: dict = Depends(verify_token)
):

    if int(current_user["sub"]) != user_id:

        raise HTTPException(
            status_code=403,
            detail="You can only delete your own account"
        )

    async with httpx.AsyncClient() as client:

        response = await client.delete(
            f"{USER_SERVICE_URL}/users/{user_id}"
        )

    return await forward_response(response)


# =========================
# PRODUCT ROUTES
# =========================

@app.get("/products")
async def get_products():

    async with httpx.AsyncClient() as client:

        response = await client.get(
            f"{PRODUCT_SERVICE_URL}/products"
        )

    return await forward_response(response)


@app.post("/products")
async def create_product(
    product: ProductRequest,
    current_user: dict = Depends(require_admin)
):

    async with httpx.AsyncClient() as client:

        response = await client.post(
            f"{PRODUCT_SERVICE_URL}/products",
            json=product.model_dump()
        )

    return await forward_response(response)


@app.put("/products/{product_id}")
async def update_product(
    product_id: int,
    product: ProductRequest,
    current_user: dict = Depends(require_admin)
):

    async with httpx.AsyncClient() as client:

        response = await client.put(
            f"{PRODUCT_SERVICE_URL}/products/{product_id}",
            json=product.model_dump()
        )

    return await forward_response(response)


@app.delete("/products/{product_id}")
async def delete_product(
    product_id: int,
    current_user: dict = Depends(require_admin)
):

    async with httpx.AsyncClient() as client:

        response = await client.delete(
            f"{PRODUCT_SERVICE_URL}/products/{product_id}"
        )

    return await forward_response(response)


# =========================
# ORDER ROUTES
# =========================

@app.post("/orders")
async def create_order(
    order: OrderRequest,
    current_user: dict = Depends(verify_token)
):

    user_id = int(current_user["sub"])

    async with httpx.AsyncClient() as client:

        response = await client.post(
            f"{ORDER_SERVICE_URL}/orders",
            json=order.model_dump(),
            headers={
                "X-User-ID": str(user_id)
            }
        )

    return await forward_response(response)
@app.get("/orders")
async def get_orders(
    current_user: dict = Depends(verify_token)
):
    user_id = int(current_user["sub"])

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{ORDER_SERVICE_URL}/orders",
            headers={
                "X-User-ID": str(user_id)
            }
        )

    return await forward_response(response)


@app.get("/orders/{order_id}")
async def get_order(
    order_id: int,
    current_user: dict = Depends(verify_token)
):
    user_id = int(current_user["sub"])

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{ORDER_SERVICE_URL}/orders/{order_id}",
            headers={
                "X-User-ID": str(user_id)
            }
        )

    return await forward_response(response)

# =========================
# CANCEL ORDER
# =========================

@app.post("/orders/{order_id}/cancel")
async def cancel_order(
    order_id: int,
    current_user: dict = Depends(verify_token)
):
    user_id = int(current_user["sub"])

    async with httpx.AsyncClient() as client:

        response = await client.post(
            f"{ORDER_SERVICE_URL}/orders/{order_id}/cancel",
            headers={
                "X-User-ID": str(user_id)
            }
        )

    return await forward_response(response)

# =========================
# UPDATE ORDER STATUS
# =========================

@app.put("/orders/{order_id}/status")
async def update_order_status(
    order_id: int,
    status: dict,
    current_user: dict = Depends(require_admin)
):
    async with httpx.AsyncClient() as client:

        response = await client.put(
            f"{ORDER_SERVICE_URL}/orders/{order_id}/status",
            json=status,
            headers={
                "X-User-ID": str(current_user["sub"])
            }
        )

    return await forward_response(response)

# =========================
# CART ROUTES
# =========================

@app.post("/cart/items")
async def add_to_cart(
    item: OrderItemRequest,
    current_user: dict = Depends(verify_token)
):
    user_id = int(current_user["sub"])

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{CART_SERVICE_URL}/cart/items",
            json=item.model_dump(),
            headers={
                "X-User-ID": str(user_id)
            }
        )

    return await forward_response(response)


@app.get("/cart")
async def get_cart(
    current_user: dict = Depends(verify_token)
):
    user_id = int(current_user["sub"])

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{CART_SERVICE_URL}/cart",
            headers={
                "X-User-ID": str(user_id)
            }
        )

    return await forward_response(response)


@app.put("/cart/items/{product_id}")
async def update_cart_item(
    product_id: int,
    item: CartItemUpdateRequest,
    current_user: dict = Depends(verify_token)
):
    user_id = int(current_user["sub"])

    async with httpx.AsyncClient() as client:
        response = await client.put(
            f"{CART_SERVICE_URL}/cart/items/{product_id}",
            json=item.model_dump(),
            headers={
                "X-User-ID": str(user_id)
            }
        )

    return await forward_response(response)


@app.delete("/cart/items/{product_id}")
async def remove_from_cart(
    product_id: int,
    current_user: dict = Depends(verify_token)
):
    user_id = int(current_user["sub"])

    async with httpx.AsyncClient() as client:
        response = await client.delete(
            f"{CART_SERVICE_URL}/cart/items/{product_id}",
            headers={
                "X-User-ID": str(user_id)
            }
        )

    return await forward_response(response)


@app.delete("/cart")
async def clear_cart(
    current_user: dict = Depends(verify_token)
):
    user_id = int(current_user["sub"])

    async with httpx.AsyncClient() as client:
        response = await client.delete(
            f"{CART_SERVICE_URL}/cart",
            headers={
                "X-User-ID": str(user_id)
            }
        )

    return await forward_response(response)

# =========================
# CHECKOUT
# =========================

@app.post("/checkout")
async def checkout(
    current_user: dict = Depends(verify_token)
):
    user_id = int(current_user["sub"])

    async with httpx.AsyncClient() as client:

        response = await client.post(
            f"{CART_SERVICE_URL}/checkout",
            headers={
                "X-User-ID": str(user_id)
            }
        )

    return await forward_response(response)