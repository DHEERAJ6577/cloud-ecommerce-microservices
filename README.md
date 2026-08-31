# Cloud E-Commerce Microservices Platform

A containerized e-commerce backend built with FastAPI, Docker, PostgreSQL, JWT authentication, and Kubernetes.

This is a hands-on microservices project created to understand how independent services communicate, how each service manages its own database, and how Kubernetes is used to deploy and manage the application.

**Architecture**

```text
                         CLIENT
                           |
                           v
                    API GATEWAY :8080
                           |
        +------------------+------------------+
        |                  |                  |
        v                  v                  v
   USER SERVICE       PRODUCT SERVICE      ORDER SERVICE
      :8000               :8001               :8002
        |                   |                   |
        v                   v                   v
     USER DB            PRODUCT DB           ORDER DB
    PostgreSQL          PostgreSQL           PostgreSQL
                                               |
                                               |
                                               v
                                         CART SERVICE
                                            :8003
                                               |
                                               v
                                            CART DB
                                           PostgreSQL

The API Gateway is the main entry point for client requests.

Each service is responsible for its own business logic and database.

Services

API Gateway

Port: 8080

The API Gateway is the main entry point to the application.

It handles authentication and routes requests to the required microservice.

User Service

Port: 8000

Handles:

User registration
Login
User accounts
User roles
JWT generation

Product Service

Port: 8001

Handles:

Product management
Product prices
Product stock
Inventory updates

Order Service

Port: 8002

Handles:

Order creation
Order status
Order cancellation
Inventory coordination

Cart Service

Port: 8003

Handles:

Shopping cart
Cart items
Checkout

Database Design

Each service has its own PostgreSQL database.

User Service
     |
     v
   userdb

Product Service
     |
     v
  productdb

Order Service
     |
     v
   orderdb

Cart Service
     |
     v
   cartdb

Services do not directly access each other's database tables.

They communicate through APIs.

Authentication

The application uses JWT authentication.

User
  |
  | Login
  v
User Service
  |
  | JWT Token
  v
API Gateway
  |
  | Verify Token
  v
Authenticated Request

The API Gateway extracts the user ID from the JWT and passes it to internal services using the X-User-ID header.

The application supports two roles:

Customer

Admin

Customers can manage their account, view products, manage their cart, checkout, view their orders, and cancel their own pending orders.

Admins can manage products and update order status.

Order Management

Orders follow this lifecycle:

             pending
                |
        +-------+-------+
        |               |
        v               v
    confirmed       cancelled
        |
        v
    completed

Cart and Checkout

Adding an item to the cart does not reduce stock.

Stock is reduced only when checkout successfully creates an order.

The checkout process is:

Customer
   |
   v
Cart Service
   |
   | Checkout
   v
Order Service
   |
   +----> Check Product
   |
   +----> Check Stock
   |
   +----> Get Current Price
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

Inventory Management

The Product Service owns the inventory.

The Order Service communicates with the Product Service to reduce or restore stock.

The Order Service does not directly access the Product database.

Compensating Action

The project demonstrates a simple compensating action.

Reduce Stock
     |
     v
Create Order
     |
   +---+---+
   |       |
Success   Failure
   |       |
   v       v
 Done   Restore Stock

If order creation fails after stock has been reduced, the application attempts to restore the stock.

This is a compensating action, not a distributed database transaction.

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

Technology Stack

Python
FastAPI
Pydantic
SQLAlchemy
HTTPX
PostgreSQL
JWT
Argon2
Docker
Docker Compose
Kubernetes
Kind
Kustomize
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
|   +-- user-service/
|   +-- product-service/
|   +-- order-service/
|   +-- cart-service/
|
+-- infrastructure/
    +-- kubernetes/
        +-- namespace/
        +-- config/
        +-- databases/
        +-- services/
        +-- kustomization.yaml

Running with Docker Compose

Clone the repository:

git clone https://github.com/DHEERAJ6577/cloud-ecommerce-microservices.git
cd cloud-ecommerce-microservices

Create the environment file:

Copy-Item .env.example .env

Start the application:

docker compose up -d --build

Check the containers:

docker ps

Open the API documentation:

http://localhost:8080/docs

Running with Kubernetes

The application has also been deployed locally using Kubernetes with Kind.

The Kubernetes setup contains:

Kind Cluster
     |
     v
ecommerce Namespace
     |
     +----> API Gateway
     |
     +----> User Service
     |
     +----> Product Service
     |
     +----> Order Service
     |
     +----> Cart Service
     |
     +----> PostgreSQL Databases

Kubernetes Services

The API Gateway uses NodePort because it is the entry point for external requests.

The internal microservices use ClusterIP.

Client
  |
  v
API Gateway
NodePort
  |
  +----> User Service
  |
  +----> Product Service
  |
  +----> Order Service
  |
  +----> Cart Service

NodePort provides external access to the application.

ClusterIP provides internal communication between services.

Persistent Storage

Each PostgreSQL database has its own PersistentVolumeClaim.

User PostgreSQL
      |
      v
user-postgres-pvc

Product PostgreSQL
      |
      v
product-postgres-pvc

Order PostgreSQL
      |
      v
order-postgres-pvc

Cart PostgreSQL
      |
      v
cart-postgres-pvc

This keeps database storage separate for each service.

Health Checks

The application services use Kubernetes readiness and liveness probes.

Readiness Probe
      |
      v
Is the service ready to receive traffic?

Liveness Probe
      |
      v
Is the application still healthy?

The services use the /health endpoint for these checks.

Self-Healing

Kubernetes maintains the desired number of Pods.

Desired state
1 Pod
   |
   v
Pod crashes
   |
   v
Actual state becomes 0
   |
   v
Kubernetes creates a replacement Pod
   |
   v
New Pod becomes Ready

The API Gateway Pod was manually deleted during testing and Kubernetes automatically created a replacement Pod.

Scaling

The Product Service was tested with two replicas.

Product Service
      |
      +----> Product Pod 1
      |
      +----> Product Pod 2

Scale the Product Service:

kubectl scale deployment product-service --replicas=2 -n ecommerce

Check the Pods:

kubectl get pods -n ecommerce -l app=product-service

Kustomize

Kustomize is used to manage the Kubernetes configuration.

Instead of applying every YAML file separately:

Kubernetes YAML files
        |
        v
kustomization.yaml
        |
        v
kubectl apply -k

Validate the configuration:

kubectl kustomize .\infrastructure\kubernetes

Deploy the configuration:

kubectl apply -k .\infrastructure\kubernetes

Kubernetes Secrets

Sensitive values such as database credentials and JWT secrets are not committed to GitHub.

Example Secret files are included for reference.

The real Secret files are ignored by Git.

Testing

The Kubernetes deployment was tested for:

Service discovery
ClusterIP communication
NodePort access
Persistent storage
Readiness probes
Liveness probes
Self-healing
Scaling
Microservice communication
End-to-end checkout

End-to-End Checkout Test

The complete checkout process was successfully tested inside Kubernetes.

Example:

Wireless Mouse
Price: 2500

First checkout:

Quantity: 2
Total: 5000

Stock:
17 -> 15

Second checkout:

Quantity: 1
Total: 2500

Stock:
15 -> 14

The orders were stored in the Order database and the cart was cleared after checkout.

The complete flow was:

Cart Service
     |
     v
Order Service
     |
     v
Product Service
     |
     v
Stock Updated
     |
     v
Order Created
     |
     v
Cart Cleared

Swagger Documentation

Main API documentation:

http://localhost:8080/docs

Other services:

http://localhost:8000/docs
http://localhost:8001/docs
http://localhost:8002/docs
http://localhost:8003/docs

Future Improvements

React frontend
GitHub Actions CI/CD
Prometheus and Grafana
Centralized logging
Improved monitoring
More advanced Kubernetes networking

Author

Dheeraj Kumar

A hands-on cloud-native microservices project focused on FastAPI, Docker, PostgreSQL, Kubernetes, authentication, service communication, and deployment.