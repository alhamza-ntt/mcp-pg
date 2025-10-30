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


#SAP MCP with planned order api from SAP API Business Hub and  authenticated client

headerss = {
    "APIKey": os.getenv("SAP_APIKey"),
    "Accept": "application/json",
    "DataServiceVersion": "2.0",
}

client = httpx.AsyncClient(
    base_url="https://sandbox.api.sap.com/s4hanacloud/sap/opu/odata/sap",
    headers=headerss,
    timeout=30.0,
)


with open("specs/API_PLANNED_ORDERS.json", "r") as f:
    spec = json.load(f)

for path, methods in spec.get("paths", {}).items():
    for method, op in methods.items():
        # skip if it's not an HTTP method definition
        if not isinstance(op, dict):
            continue

        if "operationId" not in op:
            clean_path = path.strip("/").replace("/", "_").replace("{", "").replace("}", "")
            op["operationId"] = f"{method}_{clean_path or 'root'}"


mcp = FastMCP.from_openapi(
    openapi_spec=spec,
    client=client,
    name="Planned Orders MCP",
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
