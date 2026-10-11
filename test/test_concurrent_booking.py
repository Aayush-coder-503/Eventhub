import asyncio
import os

import httpx
import pytest


BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")
API_PREFIX = "/api/v1"

EVENT_ID = os.environ["EVENT_ID"]
TOKEN_A = os.environ["TOKEN_A"]
TOKEN_B = os.environ["TOKEN_B"]


@pytest.mark.asyncio
async def test_two_users_cannot_book_same_remaining_seats():

    start_event = asyncio.Event()

    async def book_seats(client, token):
        await start_event.wait()

        return await client.post(
            f"{BASE_URL}{API_PREFIX}/book-seat/{EVENT_ID}",
            headers={
                "Authorization": f"Bearer {token}",
            },
            json={"seats": 2},
        )

    async with httpx.AsyncClient(timeout=60.0) as client:
        task_a = asyncio.create_task(
            book_seats(client, TOKEN_A)
        )
        task_b = asyncio.create_task(
            book_seats(client, TOKEN_B)
        )

        # Release both requests to compete for the same seats.
        start_event.set()

        response_a, response_b = await asyncio.gather(
            task_a,
            task_b,
        )

    responses = {
        "Attendee A": response_a,
        "Attendee B": response_b,
    }

    for name, response in responses.items():
        print(f"\n{name}")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")

    status_codes = [
        response.status_code
        for response in responses.values()
    ]

    # Fail with a useful message if the route or resource is missing.
    assert 404 not in status_codes, (
        "Received 404 Not Found. Verify the endpoint path, "
        f"event ID, and database. Responses: "
        f"{[(r.status_code, r.text) for r in responses.values()]}"
    )

    successful = sum(
        status in (200, 201)
        for status in status_codes
    )

    conflicts = status_codes.count(409)

    assert successful == 1, (
        f"Expected 1 successful booking, got {successful}. "
        f"Status codes: {status_codes}"
    )

    assert conflicts == 1, (
        f"Expected 1 HTTP 409 Conflict, got {conflicts}. "
        f"Status codes: {status_codes}"
    )
