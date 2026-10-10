import asyncio
import httpx

BASE_URL = "http://127.0.0.1:8000"

EVENT_ID = "00842a4a-697c-48b2-bf95-d793ef58f032"

#Aayush
TOKEN_A = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIzODgwYmUxMi04YmEwLTQ4YzktODZiNi02MGJmMDExZmEwNzQiLCJ0eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzkxNjUwMjI5fQ.qp7jprjXlGt1jr2_n1srV3nf3Hw9SPOqTMZTWmDVTNE"

#Harvansh
TOKEN_B = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI5NTk4MWUzNy01OWI2LTRiNDYtYTJhMi01Y2NkMzg3OTU1ZTUiLCJ0eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzkxNjUwMzA4fQ.8S2AfJKHb_oUamayQhRIUC8-xy6eWwz81y1176SQHGs"


async def book_seats(client, token, request_name, start_event):
    await start_event.wait()

    try:
        response = await client.post(
            f"{BASE_URL}/book-seat/{EVENT_ID}",
            headers={"Authorization": f"Bearer {token}"},
            json={"seats": 2},
        )

        return {
            "request": request_name,
            "status_code": response.status_code,
            "response": response.text,
        }

    except httpx.TimeoutException as exc:
        return {
            "request": request_name,
            "status_code": None,
            "response": f"Request timed out: {exc}",
        }

    except httpx.RequestError as exc:
        return {
            "request": request_name,
            "status_code": None,
            "response": f"Request failed: {exc}",
        }

async def main():
    start_event = asyncio.Event()

    async with httpx.AsyncClient(timeout=60.0) as client:
        # Prepare both requests before releasing either one.
        task_a = asyncio.create_task(
            book_seats(client, TOKEN_A, "Attendee A", start_event)
        )

        task_b = asyncio.create_task(
            book_seats(client, TOKEN_B, "Attendee B", start_event)
        )

        # Release both requests to run concurrently.
        start_event.set()

        results = await asyncio.gather(task_a, task_b)

    for result in results:
        print(f"\n{result['request']}")
        print(f"HTTP status: {result['status_code']}")
        print(f"Response: {result['response']}")

    successful = sum(
        result["status_code"] in (200, 201)
        for result in results
    )

    conflicts = sum(
        result["status_code"] == 409
        for result in results
    )

    print("\n--- TEST SUMMARY ---")
    print(f"Successful bookings: {successful}")
    print(f"Conflict responses: {conflicts}")

    if successful == 1 and conflicts == 1:
        print("PASS: One booking succeeded and the other was rejected.")
    else:
        print(
            "CHECK: Results differ from the expected outcome. "
            "Verify the test data and inspect the responses."
        )


if __name__ == "__main__":
    asyncio.run(main())
