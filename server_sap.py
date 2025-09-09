import httpx
from fastmcp import FastMCP
import json
import os
from fastapi import Request
from fastapi.responses import JSONResponse, PlainTextResponse
import uvicorn
import asyncio
from utils import perform_tool_transformation
from dotenv import load_dotenv
load_dotenv()


headerss = {
    "APIKey": os.getenv("SAP_APIKey"),
    "Accept": "application/json",
    "DataServiceVersion": "2.0",
}

client = httpx.AsyncClient(
    base_url="https://sandbox.api.sap.com/successfactors/odata/v2",
    headers=headerss,
    timeout=30.0,
)


with open("specs/payrol_converted.json", "r") as f:
    spec = json.load(f)


mcp = FastMCP.from_openapi(
    openapi_spec=spec,
    client=client,
    name="SAP MCP",
    stateless_http=True,          
    json_response=True            
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
    asyncio.run(perform_tool_transformation(mcp))
    mcp.run(transport="streamable-http", host=host, port=port, path="/mcp")
