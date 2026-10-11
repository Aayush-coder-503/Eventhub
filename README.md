# EventHub — Event Booking Backend

EventHub is a backend API for an event-booking platform. It allows organizers to create and manage events, attendees to discover events and reserve seats, and administrators to manage categories and oversee booking activity.

Built with **FastAPI, SQLAlchemy, PostgreSQL, and Alembic**, this project focuses on practical backend engineering: authentication, role-based authorization, relational data integrity, database migrations, and concurrency-safe booking operations.

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [Database Migrations](#database-migrations)
- [Running the Application](#running-the-application)
- [API Documentation](#api-documentation)
- [Authentication and Authorization](#authentication-and-authorization)
- [Events and Bookings](#events-and-bookings)
- [Concurrency and Booking Safety](#concurrency-and-booking-safety)
- [Running Tests](#running-tests)
- [Docker](#docker)
- [Useful Commands](#useful-commands)
- [Engineering Decisions](#engineering-decisions)
- [Potential Improvements](#potential-improvements)
- [Contributing](#contributing)
- [License](#license)

## Features

### Authentication and security

- User registration and login.
- Password hashing with bcrypt.
- JWT-based access and refresh tokens.
- Authentication for protected endpoints.
- Role-based authorization.
- User identity resolved from validated access tokens.

### Role-based access control

EventHub has three application roles:

| Role        | Responsibilities                                                                                   |
| ----------- | -------------------------------------------------------------------------------------------------- |
| `ADMIN`     | Manage event categories and access administrative booking information, where permitted by the API. |
| `ORGANIZER` | Create and manage their own events and view bookings associated with those events.                 |
| `ATTENDEE`  | Discover events, reserve seats, and manage their own bookings.                                     |

Authorization is enforced by the backend. Hiding a button or page in a frontend is not a substitute for server-side authorization.

### Event management

Events can contain information such as:

- Title and description
- Venue
- Start and end times
- Capacity and price
- Category
- Publication status
- Organizer ownership

The event model includes statuses such as `Draft`, `Published`, and `Cancelled`.

### Booking management

The booking workflow is designed around important business rules:

- A booking must not exceed available capacity.
- A user must not create duplicate bookings for the same event when the application’s uniqueness rule applies.
- New bookings must be rejected for past or cancelled events.
- Users must only manage bookings they are authorized to access.
- Event capacity must not be reduced below the number of seats already booked.
- Simultaneous booking attempts must not oversell an event.

### Database and testing

- PostgreSQL persistence.
- SQLAlchemy database models and sessions.
- Asynchronous database access using `asyncpg`.
- Alembic schema migrations.
- Transactional booking operations and row locking.
- Pytest test suite, including a concurrent-booking test.

## Tech Stack

| Technology     | Purpose                                   |
| -------------- | ----------------------------------------- |
| Python         | Backend language                          |
| FastAPI        | REST API framework                        |
| SQLAlchemy 2.x | ORM and database access                   |
| PostgreSQL     | Relational database                       |
| `asyncpg`      | Asynchronous PostgreSQL driver            |
| `psycopg`      | Synchronous PostgreSQL driver, where used |
| Alembic        | Database schema migrations                |
| Pydantic       | Request validation and data schemas       |
| JWT library    | Token creation and validation             |
| bcrypt         | Password hashing                          |
| Uvicorn        | ASGI application server                   |
| pytest         | Automated tests                           |
| Neon           | Hosted PostgreSQL option                  |

The installed dependency versions are defined in `requirements.txt`.

## Architecture

EventHub separates HTTP handling, business logic, validation, database models, and database connectivity.

```text
Client
  |
  | HTTP request
  v
FastAPI application (main.py)
  |
  v
Routers
  |  Request handling, dependencies, HTTP responses
  v
Services
  |  Business rules, authorization, transactions
  v
SQLAlchemy
  |  Database sessions and queries
  v
PostgreSQL
```

### Layer responsibilities

- **`routers/`** — Defines API endpoints and handles HTTP requests and responses.
- **`services/`** — Contains application business logic and database operations.
- **`schemas/`** — Defines and validates request and response data using Pydantic.
- **`models/`** — Defines SQLAlchemy database models.
- **`core/security/`** — Provides authentication dependencies and security utilities.
- **`db/`** — Configures database engines and sessions.
- **`alembic/`** — Stores versioned database migrations.
- **`test/`** — Contains automated tests.
- **`main.py`** — Application entry point and router registration.

## Project Structure

The following tree reflects the repository structure used during development. The `alembic/versions/` directory contains the individual migration files.

```text
eventhub/
├── alembic/
│   ├── versions/                  # Database migration scripts
│   ├── env.py                     # Alembic environment configuration
│   ├── README
│   └── script.py.mako             # Migration template
│
├── core/
│   └── security/
│       ├── __init__.py
│       ├── dependencies.py        # Authentication dependencies
│       └── security.py            # JWT and password security utilities
│
├── db/
│   └── db.py                      # Database engines and sessions
│
├── models/
│   ├── userModels.py              # User model
│   ├── categoryModels.py          # Category model
│   ├── eventModels.py             # Event model
│   └── bookingModels.py           # Booking model
│
├── routers/
│   ├── __init__.py
│   ├── authRoutes.py               # Registration and login routes
│   ├── categoryRoutes.py           # Category routes
│   ├── eventRoutes.py              # Event routes
│   ├── bookingRoutes.py            # Booking routes
│   └── profileRoutes.py            # Profile routes
│
├── schemas/
│   ├── __init__.py
│   ├── authSchema.py               # Authentication schemas
│   ├── categorySchema.py           # Category schemas
│   ├── eventSchema.py              # Event schemas
│   ├── editeventSchema.py          # Event update schemas
│   └── bookingSchema.py            # Booking schemas
│
├── services/
│   ├── __init__.py
│   ├── authServices.py             # Authentication business logic
│   ├── categoryServices.py         # Category business logic
│   ├── eventServices.py            # Event business logic
│   ├── bookingServices.py          # Booking business logic
│   └── profileServices.py          # Profile business logic
│
├── test/
│   └── test_concurrent_booking.py  # Concurrent booking test
│
├── .dockerignore
├── .env                           # Local secrets; do not commit
├── .env.examples                  # Environment variable example
├── .gitignore
├── Dockerfile
├── compose.yaml
├── alembic.ini
├── main.py
├── requirements.txt
├── README.md
└── Todo
```

## Prerequisites

Before starting, install:

- Python 3.12 or another version supported by the dependencies.
- Git.
- Access to a PostgreSQL database, either local or hosted.

The commands below are for Linux/macOS and use the `requirements.txt` file present in the repository.

## Getting Started

### 1. Clone the repository

```bash
git clone <YOUR_REPOSITORY_URL>
cd eventhub
```

Replace `<YOUR_REPOSITORY_URL>` with the actual Git repository URL.

### 2. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell, activate the environment with:

```powershell
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a local `.env` file using `.env.examples` as a reference. At minimum, the project expects the following settings:

```env
DATABASE_URL=
DATABASE_SYNC_URL=
JWT_SECRET=
```

Use the actual connection details and secret values for your environment. See [Environment Variables](#environment-variables) below.

### 5. Apply database migrations

Once the database URLs are configured and the database is reachable, run:

```bash
alembic upgrade head
```

This applies the migration chain to the latest revision. If this is a fresh database and migration fails, review the migration error and revision history before making changes to migration files.

### 6. Start the development server

```bash
uvicorn main:app --reload
```

The API will normally be available at:

- API base: `http://127.0.0.1:8000`
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## Environment Variables

| Variable            | Purpose                                                                |
| ------------------- | ---------------------------------------------------------------------- |
| `DATABASE_URL`      | Asynchronous PostgreSQL connection URL, typically using `asyncpg`.     |
| `DATABASE_SYNC_URL` | Synchronous PostgreSQL connection URL, using `psycopg` where required. |
| `JWT_SECRET`        | Secret used to sign and verify JWTs.                                   |

### PostgreSQL connection URL formats

An asynchronous URL generally has this form:

```env
DATABASE_URL=postgresql+asyncpg://USERNAME:PASSWORD@HOST:PORT/DATABASE
```

A synchronous psycopg URL generally has this form:

```env
DATABASE_SYNC_URL=postgresql+psycopg://USERNAME:PASSWORD@HOST:PORT/DATABASE
```

Use the exact connection details provided by your PostgreSQL host. If using Neon, copy the connection details from your Neon project and ensure the driver prefix matches the driver configured by the application.

If a database password contains reserved URL characters, URL-encode those characters in the URL.

### Generate a JWT secret

Generate a strong random secret with Python:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Put the generated value in `.env`:

```env
JWT_SECRET=replace_with_generated_secret
```

Do not commit `.env`, real database credentials, or production secrets. Ensure `.gitignore` excludes secret-bearing environment files while retaining `.env.examples`.

The application and Alembic must load the expected environment variables. If the project uses a dotenv loader, make sure it is installed and configured as required by the current code.

## Database Migrations

EventHub uses Alembic to track and apply database schema changes.

### Apply all pending migrations

```bash
alembic upgrade head
```

### Check the current database revision

```bash
alembic current
```

### View migration history

```bash
alembic history
```

### Generate a migration after changing a model

```bash
alembic revision --autogenerate -m "describe the schema change"
```

For example:

```bash
alembic revision --autogenerate -m "add booking constraint"
```

Review the generated migration before applying it. Autogeneration does not catch every schema change and should not be treated as a substitute for review.

### Roll back one revision

```bash
alembic downgrade -1
```

Use downgrades carefully, especially when a migration may remove data.

### Recommended migration workflow

1. Update the relevant SQLAlchemy model.
2. Generate a migration.
3. Review the migration operations and dependencies.
4. Apply it to a development database.
5. Test the affected behavior.
6. Commit the model change and migration together.

Avoid editing migrations that have already been applied to shared databases. Create a new migration for subsequent schema changes.

## Running the Application

For local development, run:

```bash
uvicorn main:app --reload
```

To run without automatic reload:

```bash
uvicorn main:app
```

To make the development server reachable from other devices on a trusted local network:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

Do not treat the development server as a production deployment configuration.

## API Documentation

FastAPI generates interactive API documentation from the registered routes and Pydantic schemas.

With the server running, open:

- **Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

Swagger UI lets you inspect endpoint schemas, submit requests, and test protected routes with an access token.

### Endpoint groups

The repository has separate routers for these areas:

| Router module       | Responsibility          |
| ------------------- | ----------------------- |
| `authRoutes.py`     | Registration and login  |
| `profileRoutes.py`  | User profile operations |
| `categoryRoutes.py` | Category operations     |
| `eventRoutes.py`    | Event operations        |
| `bookingRoutes.py`  | Booking operations      |

Use `/docs` or inspect the router files to confirm the exact HTTP methods, paths, request bodies, and response codes. This README deliberately avoids listing unverified endpoint paths.

## Authentication and Authorization

The general authentication flow is:

1. A user registers with the required account details.
2. The application validates the request and hashes the password.
3. The user submits login credentials.
4. The application verifies the credentials and issues tokens.
5. The client sends the access token with protected requests.
6. The backend validates the token and resolves the current user.
7. The application checks the user's role and ownership permissions before performing restricted operations.

### Access and refresh tokens

- **Access token:** Sent with protected API requests and validated by the backend.
- **Refresh token:** Used by a supported refresh flow to obtain a new access token.

Token expiration, refresh behavior, and revocation depend on the implementation in the security and authentication modules. Clients should follow the behavior implemented by the API.

### Authorization principles

Protected operations should verify both the user's role and the resource they are trying to access. For example, an organizer should not be able to update another organizer's event simply by changing an event ID in the request.

## Events and Bookings

### Event management

Event data includes fields such as title, description, venue, start time, end time, capacity, price, status, category, and organizer.

Event operations should validate incoming data, verify the requester's permissions, and preserve database integrity. Capacity updates must account for existing bookings.

### Booking rules

A booking request should be checked against current event availability inside a transaction. The application should reject invalid requests, including requests that exceed capacity or target an event that cannot accept bookings.

Booking ownership must also be enforced when viewing or cancelling reservations.

The exact request and response schemas are available in Swagger UI and the files under `schemas/`.

## Concurrency and Booking Safety

A booking system must handle more than one request at a time. Checking seat availability without coordinating concurrent requests can cause a race condition.

Imagine an event has two seats remaining and two attendees attempt to reserve both seats at nearly the same time. If both requests read the same availability before either transaction commits, both could incorrectly believe that the seats are available.

### Transaction and row-locking approach

EventHub's booking implementation uses a database transaction and row locking to coordinate access to the event's availability.

Conceptually, the flow is:

```text
Receive booking request
        |
        v
Validate request and user
        |
        v
Begin transaction
        |
        v
Lock the relevant event row
        |
        v
Read current availability
        |
        v
Validate booking constraints
        |
        v
Create booking / update related data
        |
        v
Commit transaction
```

A competing transaction must wait for the relevant lock to be released before it can proceed with its own availability check. This approach helps prevent competing requests from consuming the same remaining seats, provided all booking paths follow the same locking and transaction rules.

Important invariants include:

1. Active reservations do not exceed event capacity.
2. Duplicate bookings are rejected according to the application's uniqueness rule.
3. Past or cancelled events cannot receive new bookings.
4. Related database changes succeed or fail together.
5. Users can only manage bookings they are authorized to access.
6. Event capacity cannot be reduced below the number of seats already booked.

Database constraints should reinforce critical invariants wherever possible. Application-level checks alone may not protect every alternate code path or race condition.

## Running Tests

Activate the virtual environment before running tests.

Run the full suite:

```bash
pytest
```

Run with verbose output:

```bash
pytest -v
```

Show output printed by tests:

```bash
pytest -v -s
```

### Concurrent booking test

The repository contains:

```text
test/test_concurrent_booking.py
```

The test uses environment variables for the event and two attendee access tokens. From the project root on Linux, set them in your terminal:

```bash
export EVENT_ID="your-test-event-uuid"
export TOKEN_A="your-first-test-user-access-token"
export TOKEN_B="your-second-test-user-access-token"
```

Replace the placeholders with values from your test setup, then run:

```bash
pytest -v -s test/test_concurrent_booking.py
```

These variables must be set in the same shell session from which pytest is launched, or otherwise be provided to the test process.

Use a dedicated test database and test accounts. Ensure the event has the capacity and initial booking state expected by the test. For a meaningful concurrency check, arrange simultaneous requests that compete for the same limited remaining seats, then verify both the HTTP results and the final database state.

**Never use production access tokens or run destructive concurrency tests against production data.** Avoid committing tokens to the repository.

### Suggested test coverage

| Area           | What to test                                                 |
| -------------- | ------------------------------------------------------------ |
| Authentication | Registration, login, password verification, token validation |
| Authorization  | Role restrictions and resource ownership                     |
| Events         | Creation, updates, status validation, capacity rules         |
| Bookings       | Successful booking, duplicate prevention, cancellation       |
| Availability   | Correct remaining-seat calculations                          |
| Concurrency    | No overbooking under simultaneous requests                   |
| Migrations     | Schema upgrades work on a clean test database                |

## Docker

The repository contains a `Dockerfile`, `compose.yaml`, and `.dockerignore`, so Docker-based execution may be configured.

The exact service names, ports, environment loading, and database setup depend on the contents of those files. Inspect them before relying on a particular Compose command.

To start services when the Compose configuration is complete:

```bash
docker compose up --build
```

To stop the services:

```bash
docker compose down
```

Do not add real secrets to the Docker image or commit them in Compose configuration. Use an appropriate environment file or deployment secret mechanism. Confirm whether migrations run automatically in the container setup or must be run separately.

## Useful Commands

| Task                       | Command                                        |
| -------------------------- | ---------------------------------------------- |
| Create virtual environment | `python3 -m venv .venv`                        |
| Activate on Linux/macOS    | `source .venv/bin/activate`                    |
| Install dependencies       | `pip install -r requirements.txt`              |
| Run development server     | `uvicorn main:app --reload`                    |
| Run all tests              | `pytest`                                       |
| Run tests verbosely        | `pytest -v -s`                                 |
| Run concurrency test       | `pytest -v -s test/test_concurrent_booking.py` |
| Apply migrations           | `alembic upgrade head`                         |
| Check current revision     | `alembic current`                              |
| View migration history     | `alembic history`                              |
| Generate migration         | `alembic revision --autogenerate -m "message"` |
| Roll back one revision     | `alembic downgrade -1`                         |
| Start Docker Compose       | `docker compose up --build`                    |
| Stop Docker Compose        | `docker compose down`                          |

## Engineering Decisions

### FastAPI

FastAPI provides request validation, dependency injection, asynchronous endpoint support, and automatically generated API documentation.

### SQLAlchemy and async database access

SQLAlchemy provides ORM models and transaction management. Asynchronous access through `asyncpg` is useful for I/O-bound database operations, provided sessions and transactions are managed correctly.

### PostgreSQL

PostgreSQL provides relational constraints, transactions, and row-level locking. These features are important when concurrent requests compete for limited event capacity.

### Alembic

Alembic makes schema changes versioned and reviewable. Migrations help keep development, testing, and deployment databases aligned with the application's models.

### Routers and services

Separating routers from services keeps HTTP concerns separate from business rules. This makes the code easier to reason about, test, and extend.

### Concurrency testing

A booking endpoint may work correctly in a single request and still fail under simultaneous traffic. A dedicated concurrency test helps validate the behavior of transaction and locking logic under competing requests.

## Potential Improvements

Possible future enhancements include:

- Broader automated tests for authentication, events, and bookings.
- Database constraints and indexes for critical booking invariants.
- Pagination, sorting, and expanded event filters.
- Structured logging and consistent error handling.
- Rate limiting for sensitive endpoints.
- CI checks for tests and migration consistency.
- Production deployment, health checks, and monitoring.
- Further hardening of refresh-token lifecycle and session revocation, if needed.
- A frontend for attendees and organizers.

These are possible next steps, not claims that all such features are currently implemented.

## Contributing

Contributions and suggestions are welcome.

1. Create a branch for your change.
2. Keep HTTP handling and business logic separated.
3. Add or update tests for changed behavior.
4. Generate and review migrations when models change.
5. Run the relevant tests before submitting a pull request.

## License

No license file was present in the inspected project tree. Add a `LICENSE` file and update this section before distributing the project under an open-source license.

---

EventHub is a backend engineering project exploring secure API design, relational data integrity, database migrations, and reliable booking behavior under concurrent workloads.
