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

 Request Flow



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


Services
API Gateway

Port: 8080

The API Gateway is the main entry point for the application.

It handles authentication and routes requests to the required microservice.

User Service

Port: 8000

Handles:

User registration
Login
User accounts
User roles
Product Service

Port: 8001

Handles:

Products
Prices
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
Database

Each microservice has its own PostgreSQL database.

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



The services do not directly share database tables.

This follows the database-per-service approach.

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


The API Gateway gets the user ID from the JWT and passes it to internal services using the X-User-ID header.

There are two roles:

Customer

Customers can:

Manage their own account
View products
Manage cart items
Checkout
View their own orders
Cancel their own pending orders
Admin

Admins can:

Manage products
Update order status
Perform administrative operations
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

The project demonstrates a simple compensating action.

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
|   |
|   +-- user-service/
|   +-- product-service/
|   +-- order-service/
|   +-- cart-service/
|
+-- infrastructure/
    |
    +-- kubernetes/
        |
        +-- namespace/
        |
        +-- config/
        |
        +-- databases/
        |
        +-- services/
        |
        +-- kustomization.yaml
Environment Setup

Create your local environment file:

Copy-Item .env.example .env

Then add your local configuration.

The real .env file is ignored by Git and should not be committed.

Running with Docker Compose

Clone the repository:

git clone https://github.com/DHEERAJ6577/cloud-ecommerce-microservices.git
cd cloud-ecommerce-microservices

Create the environment file:

Copy-Item .env.example .env

Build and start all services:

docker compose up -d --build

Check the containers:

docker ps

Main API documentation:

http://localhost:8080/docs
Kubernetes Deployment

The application is also deployed on Kubernetes using Kind.

Kubernetes Architecture
CLIENT
   |
   v
API Gateway


NodePort
   |
   +-------------------+-------------------+-------------------+
   |                   |                   |                   |
   v                   v                   v                   v
User Service      Product Service      Order Service       Cart Service
 ClusterIP           ClusterIP           ClusterIP          ClusterIP
   |                   |                   |                   |
   v                   v                   v                   v
User PostgreSQL   Product PostgreSQL   Order PostgreSQL   Cart PostgreSQL
   |                   |                   |                   |
   v                   v                   v                   v
  PVC                 PVC                 PVC                PVC
Kubernetes Tools

The project uses:

Kind for the local Kubernetes cluster
kubectl for Kubernetes management
Kustomize for deploying the complete application
Create the Kind Cluster

Create the cluster:

kind create cluster --name ecommerce-cluster

Check the cluster:

kubectl get nodes

Create the application namespace:

kubectl apply -f .\infrastructure\kubernetes\namespace\ecommerce-namespace.yaml
Kubernetes Secrets

Real Kubernetes Secret files are not committed to GitHub.

Example Secret files are provided in:

infrastructure/kubernetes/config/

Create the real Secret files locally using the example files and your own values.

The Secret files intentionally remain ignored by Git.

Deploy the Application

Kustomize can apply the Kubernetes configuration:

kubectl apply -k .\infrastructure\kubernetes

Check the Pods:

kubectl get pods -n ecommerce

Check the Services:

kubectl get services -n ecommerce

Check the PersistentVolumeClaims:

kubectl get pvc -n ecommerce
Kubernetes Services

The API Gateway is exposed using NodePort.

The internal microservices use ClusterIP.

Client
   |
   v
API Gateway
   |
   +----> User Service
   |
   +----> Product Service
   |
   +----> Order Service
   |
   +----> Cart Service

NodePort is used for external access.

ClusterIP is used for communication inside the Kubernetes cluster.

PostgreSQL Storage

Each PostgreSQL database uses its own PersistentVolumeClaim.

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
Is the service ready to receive requests?

Liveness Probe
    |
    v
Is the application still running correctly?

Each service uses its /health endpoint for these checks.

Self-Healing

Kubernetes maintains the desired number of Pods.

For example:

Desired Pods = 1
      |
      v
Pod crashes
      |
      v
Actual Pods = 0
      |
      v
Kubernetes creates a new Pod
      |
      v
New Pod becomes Ready

This project was tested by deleting the API Gateway Pod and observing Kubernetes create a replacement Pod.

Scaling

Product Service was tested with two replicas.

Product Service
      |
      +----> Product Pod 1
      |
      +----> Product Pod 2

The Kubernetes Service automatically keeps both ready Pods as endpoints.

Scale the Product Service:

kubectl scale deployment product-service --replicas=2 -n ecommerce

Check:

kubectl get pods -n ecommerce -l app=product-service
Kustomize

Instead of applying every Kubernetes file separately, the project uses Kustomize.

Apply the complete Kubernetes configuration with:

kubectl apply -k .\infrastructure\kubernetes

Validate the generated configuration without applying it:

kubectl kustomize .\infrastructure\kubernetes
Kubernetes Testing

The Kubernetes deployment was tested through the following flow:

API Gateway
     |
     v
User Service
     |
     v
Product Service
     |
     v
Cart Service
     |
     v
Order Service

The checkout flow was also tested successfully.

Example:

Product Stock
17
 |
 | Checkout
 v
15

A second checkout reduced the stock further:

15
 |
 | Checkout
 v
14

Orders were created successfully and the cart was cleared after checkout.

Swagger Documentation

Main API documentation:

http://localhost:8080/docs

Other service documentation:

http://localhost:8000/docs
http://localhost:8001/docs
http://localhost:8002/docs
http://localhost:8003/docs

For Kubernetes, services are normally accessed internally using their Kubernetes Service names.

Future Improvements

Possible future improvements include:

React frontend
GitHub Actions CI/CD
Prometheus and Grafana
Improved monitoring and logging
More advanced Kubernetes networking
Author

Dheeraj Kumar

Built as a hands-on project to learn microservices, Docker, APIs, authentication, databases, and cloud-native application development.