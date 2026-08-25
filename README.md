# Cloud E-Commerce Microservices Platform

A simple e-commerce backend built using FastAPI, Docker, PostgreSQL, JWT authentication, and microservices.

This project was built as a hands-on learning project to understand how different microservices communicate with each other while maintaining their own databases.

## Architecture

![Cloud E-Commerce Microservices Architecture](docs/architecture.png)

The application contains four main services:

- User Service
- Product Service
- Order Service
- Cart Service

All requests from the client go through the API Gateway.

Each service has its own PostgreSQL database.

### Request Flow

```text
                         CLIENT
                           |
                           v
                  API Gateway :8080
                           |
        +------------------+------------------+
        |                  |                  |
        v                  v                  v
 User Service       Product Service      Order Service
    :8000                :8001               :8002
        |                  |                  |
        v                  v                  v
    User DB            Product DB          Order DB
   PostgreSQL          PostgreSQL          PostgreSQL
     :5433                :5434              :5435
                                               ^
                                               |
                                               | HTTP
                                               |
                                        Cart Service
                                           :8003
                                               |
                                               v
                                           Cart DB
                                          PostgreSQL
                                            :5436
Services

API Gateway - Port 8080

Main entry point for the application.

Handles authentication and sends requests to the correct service.

User Service - Port 8000

Handles:

User registration
Login
User accounts
User roles

Product Service - Port 8001

Handles:

Products
Prices
Product stock

Order Service - Port 8002

Handles:

Order creation
Order status
Order cancellation
Inventory coordination

Cart Service - Port 8003

Handles:

Shopping cart
Cart items
Checkout
Database

Each service has its own PostgreSQL database.

User Service
    |
    v
userdb :5433

Product Service
    |
    v
productdb :5434

Order Service
    |
    v
orderdb :5435

Cart Service
    |
    v
cartdb :5436

The services do not directly share database tables.

Authentication

The application uses JWT authentication.

User Login
    |
    v
User Service
    |
    v
JWT Token
    |
    v
API Gateway
    |
    v
Authenticated Request

The API Gateway gets the user ID from the JWT and passes it to the internal services using the X-User-ID header.

There are two roles:

Customer
Admin

Customers can manage their own account, cart, and orders.

Admins can manage products and update order status.

Order Management

Orders follow this lifecycle:

pending
   |
   +------> confirmed ------> completed
   |
   +------> cancelled

The Order Service checks the product, checks stock, gets the current price, calculates the order total, and creates the order.

Customers can cancel their own pending orders.

Admins can update order status.

Cart and Checkout

Adding a product to the cart does not reduce product stock.

Stock is reduced when checkout successfully creates the order.

Checkout Flow
Customer
   |
   v
Cart Service
   |
   | POST /checkout
   v
Order Service
   |
   +----> Check Product
   |
   +----> Check Stock
   |
   +----> Get Price
   |
   +----> Reduce Stock
   |
   +----> Create Order
   |
   v
Order Created
   |
   v
Cart Cleared
Inventory and Failure Handling

The Product Service owns the inventory.

The Order Service communicates with the Product Service to reduce or restore stock.

The Order Service does not directly access the Product database.

Compensating Action

The project also demonstrates a simple compensating action.

Reduce Stock
     |
     v
Create Order
     |
     +------> Success
     |
     +------> Failure
                |
                v
          Restore Stock

This is a compensating action and not a distributed database transaction.

API Endpoints

User Service

GET    /users
POST   /users
POST   /login
PUT    /users/{user_id}
DELETE /users/{user_id}

Product Service

GET    /products
POST   /products
PUT    /products/{product_id}
DELETE /products/{product_id}

Order Service

POST   /orders
GET    /orders
GET    /orders/{order_id}
POST   /orders/{order_id}/cancel
PUT    /orders/{order_id}/status

Cart Service

POST   /cart/items
GET    /cart
PUT    /cart/items/{product_id}
DELETE /cart/items/{product_id}
DELETE /cart
POST   /checkout
Technologies Used
Python
FastAPI
PostgreSQL
SQLAlchemy
HTTPX
JWT
Argon2
Docker
Docker Compose
Swagger / OpenAPI
Project Structure
cloud-ecommerce-microservices/
|
+-- README.md
+-- .env.example
+-- .gitignore
+-- docker-compose.yml
|
+-- docs/
|   +-- architecture.png
|
+-- api-gateway/
|
+-- services/
    |
    +-- user-service/
    +-- product-service/
    +-- order-service/
    +-- cart-service/
Environment Setup

Create your local environment file:

Copy-Item .env.example .env

Then add your local configuration.

The real .env file is ignored by Git and should not be committed.

Running the Project

Clone the repository:

git clone <your-repository-url>
cd cloud-ecommerce-microservices

Create the environment file:

Copy-Item .env.example .env

Build and start all services:

docker compose up -d --build

Check the containers:

docker ps
Swagger Documentation

Main API documentation:

http://localhost:8080/docs

Other service documentation:

http://localhost:8000/docs
http://localhost:8001/docs
http://localhost:8002/docs
http://localhost:8003/docs

The API Gateway is the main entry point for the application.

Future Improvements
React frontend
Kubernetes deployment
GitHub Actions CI/CD
Prometheus and Grafana
Cloud deployment
Author

Dheeraj Kumar

Built as a hands-on project to learn microservices, Docker, APIs, authentication, databases, and cloud-native application development