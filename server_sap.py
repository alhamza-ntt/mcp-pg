import httpx
from fastmcp import FastMCP
import json
import os

headers = {
        "APIKey": os.getenv("SAP_APIKey"),
        "Accept": "application/json",
        "DataServiceVersion": "2.0"}
params = {
        "$top": 2,
        "$select": "lastModifiedBy"}
client = httpx.AsyncClient(base_url="https://sandbox.api.sap.com/successfactors/odata/v2/EmployeeTimeSheet",
                            headers=headers,
                            params=params)

with open("payrol_converted.json", "r") as f:
    openapi_spec = f.read()
spec= json.loads(openapi_spec)


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
