import os
import httpx
from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse


client = httpx.Client(base_url="https://jsonplaceholder.typicode.com")

openapi_spec = {
    "openapi": "3.0.0",
    "info": {"title": "JSONPlaceholder API", "version": "1.0"},
    "paths": {
        "/users": {"get": {"summary": "Get all users", "operationId": "get_users",
                           "responses": {"200": {"description": "A list of users."}}}},
        "/users/{id}": {"get": {"summary": "Get a user by ID", "operationId": "get_user_by_id",
                                "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}],
                                "responses": {"200": {"description": "A single user."}}}},
        "/posts": {"get": {"summary": "Get all posts", "operationId": "get_posts",
                           "responses": {"200": {"description": "A list of posts."}}}},
        "/posts/{id}": {"get": {"summary": "Get a post by ID", "operationId": "get_post_by_id",
                                "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}],
                                "responses": {"200": {"description": "A single post."}}}},
    },
}

mcp = FastMCP.from_openapi(
    openapi_spec=openapi_spec,
    client=client,
    name="JSONPlaceholder MCP Server"
)

# Health check and root landing
@mcp.custom_route("/healthz", methods=["GET"])
async def healthz(_: Request) -> PlainTextResponse:
    return PlainTextResponse("OK")

@mcp.custom_route("/", methods=["GET"])
async def root(_: Request) -> JSONResponse:
    return JSONResponse({"status": "ok", "mcp_endpoint": "/mcp"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    host = os.environ.get("HOST", "0.0.0.0")
    mcp.run(transport="http", host=host, port=port)

