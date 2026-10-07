# EventHub - Backend

EventHub is a backend for an event booking system where organizers can create and manage events, while attendees can browse events and book available seats.

I built this project to practice building a proper async backend with FastAPI, PostgreSQL, SQLAlchemy, authentication, migrations, and real-world booking rules.

## Tech Stack

- **FastAPI** — API framework
- **SQLAlchemy 2.0** — ORM
- **PostgreSQL** — Database
- **asyncpg** — Async PostgreSQL driver
- **Alembic** — Database migrations
- **Pydantic v2** — Request/response validation
- **JWT + bcrypt** — Authentication & password hashing

## What it does

### Authentication

- User registration and login
- Password hashing with bcrypt
- Access and refresh JWT tokens
- Role-based access control

There are three roles:

- **Admin** — manages categories and can view all bookings
- **Organizer** — creates, updates and manages their own events
- **Attendee** — browses events and manages their own bookings

### Events

Organizers can:

- Create events
- Update their events
- Delete/cancel their events
- See bookings for their events

Attendees can:

- Browse events
- Search by title
- Filter by category, date and price
- See remaining seats
- Book available seats
- Cancel their own bookings

### Booking Logic

The interesting part of the project is the booking system.

A booking must:

- Have enough seats available
- Not allow the same user to book the same event twice
- Not allow bookings for past or cancelled events
- Never reduce an event's capacity below the number of seats already booked

The booking operation also uses a database transaction with row locking to prevent two users from booking the same remaining seats at the same time.

## Project Structure

```text
eventhub/
│
├── alembic/          # Database migrations
├── core/
│   └── security/     # JWT and password security
├── db/               # Database connection and sessions
├── models/           # SQLAlchemy models
├── routers/          # API routes
├── schemas/          # Pydantic schemas
├── services/         # Business logic
├── test/             # Tests
│
├── alembic.ini
├── main.py
├── pyproject.toml
└── README.md
```
