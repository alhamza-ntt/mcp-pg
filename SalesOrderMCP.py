import httpx
from fastmcp import FastMCP
import json
import os
from fastapi import Request
from fastapi.responses import JSONResponse, PlainTextResponse
import asyncio
from dotenv import load_dotenv
load_dotenv()

sap_user = os.getenv("general_s4hana_user")
sap_password = os.getenv("general_s4hana_password")

headerss = {
    "Accept": "application/json",
    "DataServiceVersion": "2.0",
}

client = httpx.AsyncClient(
    base_url=os.getenv("sales_order_base_url"),
    headers=headerss,
    auth=(sap_user, sap_password),  
    timeout=30.0,
)

# Use the simplified spec
with open("specs/API_SALES_ORDER_SRV_reduced.json", "r") as f:
    spec = json.load(f)



mcp = FastMCP.from_openapi(
    openapi_spec=spec,
    client=client,
    name="Material_Stock_MCP",
    stateless_http=True,
    json_response=True
)


@mcp.custom_route("/healthz", methods=["GET"])
async def healthz(_: Request) -> PlainTextResponse:
    return PlainTextResponse("OK")

@mcp.custom_route("/", methods=["GET"])
async def root(_: Request) -> JSONResponse:
    return JSONResponse({"status": "ok", "mcp_endpoint": "/mcp"})

@mcp.custom_route("/debug_env", methods=["GET"])
async def debug_env(_: Request) -> JSONResponse:
    return JSONResponse({
        "material_stock_user": os.getenv("general_s4hana_user"),
        "material_stock_pass": os.getenv("general_s4hana_password") is not None,
        "material_stock_baseurl": os.getenv("materialstock_base_url"),
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    host = os.environ.get("HOST", "0.0.0.0")
    mcp.run(transport="streamable-http", host=host, port=port, path="/mcp")