import json

from fastapi import Request as FastAPIRequest


async def fastapi_request_adapter(payload: dict, headers: dict, route: str) -> FastAPIRequest:
    # Create a FastAPI Request object from the payload and headers
    # 1. Create the scope dictionary
    scope = {
        "type": "http",
        "method": "POST",
        "path": f"/{route}",
        "raw_path": f"/{route}".encode(),
        "query_string": b"",
        "headers": [(k.lower().encode(), v.encode()) for k, v in headers.items()],
        "client": ("127.0.0.1", 0),  # Default client address
    }

    # 2. Create a receive function that returns the request body
    body_bytes = json.dumps(payload).encode()

    async def receive():
        return {
            "type": "http.request",
            "body": body_bytes,
            "more_body": False,
        }

    # 3. Create a send function to capture the response
    response_body = []
    response_status = None
    response_headers = None

    async def send(message):
        nonlocal response_status, response_headers

        if message["type"] == "http.response.start":
            response_status = message["status"]
            response_headers = message["headers"]
        elif message["type"] == "http.response.body":
            response_body.append(message.get("body", b""))

    # 4. Create the request object
    fastapi_request = FastAPIRequest(scope, receive)

    return fastapi_request
