\# Cloud E-Commerce Microservices Platform



A containerized e-commerce backend built using \*\*FastAPI, Docker, PostgreSQL, JWT authentication, and a microservices architecture\*\*.



This project is a hands-on demonstration of cloud-native and microservices concepts including service isolation, API Gateway routing, authentication, authorization, inventory management, order processing, cart management, checkout, and compensating actions.



\---



\## Architecture



!\[Cloud E-Commerce Microservices Architecture](docs/architecture.png)



\### Architecture Overview



The system consists of four independent backend microservices:



\- User Service — user registration, login, authentication, and role management

\- Product Service — product management and inventory

\- Order Service — order creation, status management, cancellation, and inventory coordination

\- Cart Service — shopping cart management and checkout



All client requests are routed through the \*\*API Gateway\*\*.



Each microservice owns its own PostgreSQL database following the \*\*database-per-service\*\* pattern.



\### Service-to-Service Communication



```text

Client

&#x20;  |

&#x20;  v

API Gateway :8080

&#x20;  |

&#x20;  +----------------------+----------------------+----------------------+

&#x20;  |                      |                      |                      |

&#x20;  v                      v                      v                      v

User Service             Product Service        Order Service          Cart Service

:8000                        :8001                 :8002                  :8003

&#x20;  |                      |                      |                      |

&#x20;  v                      v                      v                      v

User DB                   Product DB              Order DB               Cart DB

:5433                        :5434                  :5435                  :5436



The main checkout interaction is:



Cart Service

&#x20;    |

&#x20;    | POST /checkout

&#x20;    v

Order Service

&#x20;    |

&#x20;    v

Product Service

&#x20;    |

&#x20;    v

Inventory Updated

Services

Service	Port	Responsibility

API Gateway	8080	Routing, JWT verification, authorization

User Service	8000	Users, login, JWT, roles

Product Service	8001	Products and inventory

Order Service	8002	Orders and order lifecycle

Cart Service	8003	Cart and checkout

Database Architecture



Each microservice has its own PostgreSQL database.



Service	Database	Host Port

User Service	userdb	5433

Product Service	productdb	5434

Order Service	orderdb	5435

Cart Service	cartdb	5436



The services do not directly share database tables.



Authentication and Authorization



Authentication uses JWT.



User Login

&#x20;   |

&#x20;   v

User Service

&#x20;   |

&#x20;   v

JWT Token

&#x20;   |

&#x20;   v

API Gateway

&#x20;   |

&#x20;   v

Token Verification

&#x20;   |

&#x20;   v

Authenticated Request



The API Gateway extracts the authenticated user's ID from the JWT and forwards it to internal services using:



X-User-ID

Roles

Customer



Customers can:



Manage their own account

View products

Add and manage cart items

Checkout

View their own orders

Cancel their own pending orders

Admin



Admins can:



Manage products

Update order status

Perform administrative operations through protected endpoints

Order Lifecycle



Orders follow this lifecycle:



&#x20;            +-----------+

&#x20;            |  pending  |

&#x20;            +-----+-----+

&#x20;                  |

&#x20;         +--------+--------+

&#x20;         |                 |

&#x20;         v                 v

&#x20;   +-----------+     +-----------+

&#x20;   | confirmed |     | cancelled |

&#x20;   +-----+-----+     +-----------+

&#x20;         |

&#x20;         v

&#x20;   +-----------+

&#x20;   | completed |

&#x20;   +-----------+



Valid transitions include:



pending     -> confirmed

pending     -> cancelled

confirmed   -> completed



Invalid transitions are rejected by the Order Service.



Cart and Checkout Flow

Customer

&#x20;  |

&#x20;  v

Cart Service

&#x20;  |

&#x20;  | POST /checkout

&#x20;  v

Order Service

&#x20;  |

&#x20;  +--> Validate Product

&#x20;  |

&#x20;  +--> Validate Stock

&#x20;  |

&#x20;  +--> Get Current Price

&#x20;  |

&#x20;  +--> Reduce Stock

&#x20;  |

&#x20;  +--> Create Order

&#x20;  |

&#x20;  v

Order Created

&#x20;  |

&#x20;  v

Cart Cleared



Adding an item to the cart does not reduce product inventory.



Inventory is reduced when the order is successfully created.



Inventory Management



The Product Service owns inventory.



It provides operations for:



Decrease Stock

Increase Stock



The Order Service communicates with the Product Service instead of directly modifying the Product database.



Order Service

&#x20;     |

&#x20;     | HTTP

&#x20;     v

Product Service

&#x20;     |

&#x20;     v

Product Database



This keeps service ownership boundaries clear.



Compensating Action



The project demonstrates a simple compensating-action pattern for handling failures across independent services.



Example:



Decrease Stock

&#x20;     |

&#x20;     v

Create Order

&#x20;     |

&#x20;  +--+--+

&#x20;  |     |

Success Failure

&#x20;  |     |

&#x20;  v     v

&#x20;Done  Restore Stock



If order creation fails after inventory has been reduced, the Order Service attempts to restore the affected inventory.



This is a compensating action, not a true distributed database transaction.



API Endpoints

User Service

GET    /users

POST   /users

POST   /login

PUT    /users/{user\_id}

DELETE /users/{user\_id}

Product Service

GET    /products

POST   /products

PUT    /products/{product\_id}

DELETE /products/{product\_id}

Order Service

POST   /orders

GET    /orders

GET    /orders/{order\_id}

POST   /orders/{order\_id}/cancel

PUT    /orders/{order\_id}/status

Cart Service

POST   /cart/items

GET    /cart

PUT    /cart/items/{product\_id}

DELETE /cart/items/{product\_id}

DELETE /cart

Checkout

POST   /checkout

Technology Stack

Backend

Python

FastAPI

Pydantic

SQLAlchemy

HTTPX

Database

PostgreSQL

Authentication

JWT

Argon2 password hashing

Containerization

Docker

Docker Compose

API Documentation

Swagger / OpenAPI

Project Structure

cloud-ecommerce-microservices/

|

+-- .env.example

+-- .gitignore

+-- README.md

+-- docker-compose.yml

|

+-- docs/

|   +-- architecture.png

|

+-- api-gateway/

|   +-- Dockerfile

|   +-- jwt\_auth.py

|   +-- main.py

|   +-- requirements.txt

|

+-- services/

&#x20;   |

&#x20;   +-- user-service/

&#x20;   |   +-- Dockerfile

&#x20;   |   +-- auth.py

&#x20;   |   +-- database.py

&#x20;   |   +-- jwt\_auth.py

&#x20;   |   +-- main.py

&#x20;   |   +-- models.py

&#x20;   |   +-- requirements.txt

&#x20;   |   +-- schemas.py

&#x20;   |

&#x20;   +-- product-service/

&#x20;   |   +-- Dockerfile

&#x20;   |   +-- database.py

&#x20;   |   +-- main.py

&#x20;   |   +-- models.py

&#x20;   |   +-- requirements.txt

&#x20;   |   +-- schemas.py

&#x20;   |

&#x20;   +-- order-service/

&#x20;   |   +-- Dockerfile

&#x20;   |   +-- database.py

&#x20;   |   +-- main.py

&#x20;   |   +-- models.py

&#x20;   |   +-- requirements.txt

&#x20;   |   +-- schemas.py

&#x20;   |

&#x20;   +-- cart-service/

&#x20;       +-- Dockerfile

&#x20;       +-- database.py

&#x20;       +-- main.py

&#x20;       +-- models.py

&#x20;       +-- requirements.txt

&#x20;       +-- schemas.py

Environment Configuration



The real .env file is intentionally excluded from Git.



Create your local environment file from the example:



Copy-Item .env.example .env



Then update the values for your environment.



Example structure:



JWT\_SECRET\_KEY=your-secret-key



USER\_DATABASE\_URL=postgresql://userservice:your-user-password@user-postgres:5432/userdb

PRODUCT\_DATABASE\_URL=postgresql://productservice:your-product-password@product-postgres:5432/productdb

ORDER\_DATABASE\_URL=postgresql://orderservice:your-order-password@order-postgres:5432/orderdb

CART\_DATABASE\_URL=postgresql://cartservice:your-cart-password@cart-postgres:5432/cartdb



Inside Docker Compose, PostgreSQL services are reached using their service names and the internal PostgreSQL port 5432.



Never commit the real .env file.



Running the Project

1\. Clone the repository

git clone <your-repository-url>

cd cloud-ecommerce-microservices

2\. Create the environment file

Copy-Item .env.example .env



Edit .env with your local configuration.



3\. Build and start the project

docker compose up -d --build

4\. Check running containers

docker ps

5\. Open the main API documentation

http://localhost:8080/docs

Service URLs

Service	URL

API Gateway	http://localhost:8080

User Service	http://localhost:8000

Product Service	http://localhost:8001

Order Service	http://localhost:8002

Cart Service	http://localhost:8003

Swagger Documentation

http://localhost:8080/docs

http://localhost:8000/docs

http://localhost:8001/docs

http://localhost:8002/docs

http://localhost:8003/docs



The API Gateway is the primary entry point for client requests.



PostgreSQL Ports

Database	Host Port

User PostgreSQL	5433

Product PostgreSQL	5434

Order PostgreSQL	5435

Cart PostgreSQL	5436

Key Microservices Concepts Demonstrated

Microservice decomposition

API Gateway pattern

Database-per-service pattern

REST APIs

Synchronous service-to-service communication

JWT authentication

Role-based access control

User ownership authorization

Inventory management

Order lifecycle management

Cart management

Checkout workflow

Compensating actions

Docker containerization

Docker Compose orchestration

PostgreSQL persistence

Swagger / OpenAPI

Current Project Scope



This project focuses on the backend microservices and containerized architecture.



It is intended as a hands-on learning and portfolio project demonstrating how independent services can communicate while maintaining separate databases and responsibilities.



Future Enhancements



Possible future improvements:



React frontend

Kubernetes deployment

Kubernetes Deployments and Services

ConfigMaps and Secrets

Persistent Volumes

Ingress

Horizontal Pod Autoscaling

Prometheus and Grafana

GitHub Actions CI/CD

Cloud deployment

Author



Dheeraj Kumar



A hands-on cloud-native microservices learning and portfolio project.
