import os
import httpx
from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse


#mock server with jsomplaceholder api for quick test and debugging

import httpx

async def _log_request(request: httpx.Request):
    print("→", request.method, request.url)

async def _log_response(response: httpx.Response):
    print("←", response.status_code, response.headers.get("content-type"))

client = httpx.AsyncClient(
    base_url="https://jsonplaceholder.typicode.com",
    headers={"Accept": "application/json"},
    follow_redirects=True,
    event_hooks={"request": [_log_request], "response": [_log_response]},
)



openapi_spec = {
    "openapi": "3.0.0",
    "info": {"title": "JSONPlaceholder API", "version": "1.0"},
    "servers": [{"url": "https://jsonplaceholder.typicode.com"}],
    "paths": {
        "/users": {
            "get": {
                "summary": "Get all users",
                "operationId": "get_users",
                "responses": {
                    "200": {
                        "description": "A list of users.",
                        "content": {"application/json": {}}
                    }
                }
            }
        },
        "/users/{id}": {
            "get": {
                "summary": "Get a user by ID",
                "operationId": "get_user_by_id",
                "parameters": [
                    {"name": "id", "in": "path", "required": True,
                     "schema": {"type": "string"}}
                ],
                "responses": {
                    "200": {
                        "description": "A single user.",
                        "content": {"application/json": {}}
                    }
                }
            }
        },
        "/posts": {
            "get": {
                "summary": "Get all posts",
                "operationId": "get_posts",
                "responses": {
                    "200": {
                        "description": "A list of posts.",
                        "content": {"application/json": {}}
                    }
                }
            }
        },
        "/posts/{id}": {
            "get": {
                "summary": "Get a post by ID",
                "operationId": "get_post_by_id",
                "parameters": [
                    {"name": "id", "in": "path", "required": True,
                     "schema": {"type": "string"}}
                ],
                "responses": {
                    "200": {
                        "description": "A single post.",
                        "content": {"application/json": {}}
                    }
                }
            }
        },
    },
}


mcp = FastMCP.from_openapi(
    openapi_spec=openapi_spec,
    client=client,
    name="JSONPlaceholder MCP Server",
    stateless_http=True,          # << disable MCP sessions
    json_response=True            # << simpler responses for some clients
)

@mcp.custom_route("/healthz", methods=["GET"])
async def healthz(_: Request) -> PlainTextResponse:
    return PlainTextResponse("OK")

@mcp.custom_route("/", methods=["GET"])
async def root(_: Request) -> JSONResponse:
    return JSONResponse({"status": "ok", "mcp_endpoint": "/mcp"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    host = os.environ.get("HOST", "0.0.0.0")
    # Be explicit about the modern transport and path
    mcp.run(transport="streamable-http", host=host, port=port, path="/mcp")





