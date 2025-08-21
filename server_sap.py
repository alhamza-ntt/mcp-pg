import httpx
from fastmcp import FastMCP
import json
import os
from fastapi import Request
from fastapi.responses import JSONResponse, PlainTextResponse
import uvicorn

# Build headers
headers = {
    "APIKey": os.getenv("SAP_APIKey"),
    "Accept": "application/json",
    "DataServiceVersion": "2.0",
}

# Avoid global default query params that can conflict with tool calls
client = httpx.AsyncClient(
    base_url="https://sandbox.api.sap.com/successfactors/odata/v2",
    headers=headers,
    timeout=30.0,
)

# Load OpenAPI spec as dict
with open("payrol_converted.json", "r") as f:
    spec = json.load(f)

# Give the server a meaningful name for logs
mcp = FastMCP.from_openapi(
    openapi_spec=spec,
    client=client,
    name="PayrollTimeSheet"
)

# Health check endpoint
@mcp.custom_route("/healthz", methods=["GET"])
async def healthz(_: Request) -> PlainTextResponse:
    return PlainTextResponse("OK")

# Root landing with welcome message
@mcp.custom_route("/", methods=["GET"])
async def root(_: Request) -> JSONResponse:
    return JSONResponse({
        "status": "ok",
        "mcp_endpoint": "/mcp",
        "message": "Welcome to the SAP MCP server"
    })

# Create an ASGI app in **stateless** Streamable HTTP mode
app = mcp.streamable_http_app(stateless_http=True)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    host = os.environ.get("HOST", "0.0.0.0")
    uvicorn.run(app, host=host, port=port)
