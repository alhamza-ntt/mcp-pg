import os
import json
import base64
import httpx
from dotenv import load_dotenv
from fastmcp import FastMCP
from fastapi import Request
from fastapi.responses import JSONResponse, PlainTextResponse
import asyncio

load_dotenv()

user = os.getenv("CREDUSERNAME", "")
pwd = os.getenv("CREDPASS", "")

basic_token = base64.b64encode(f"{user}:{pwd}".encode("utf-8")).decode("utf-8")
headers = {
    "Authorization": f"Basic {basic_token}",
    "Accept": "application/json",
}

client = httpx.AsyncClient(
    base_url=(
        "https://ntt-pi-dev.it-cpi001-rt.cfapps.eu10.hana.ondemand.com/"
        "http/df.nrw-sfd100-odata/zpp_workerassistant_srv/"
    ),
    headers=headers,
    timeout=30.0,
    verify=False,  # keep identical to your current setup
)

with open("specs/odata_h2b.json", "r", encoding="utf-8") as f:
    spec = json.load(f)

mcp = FastMCP.from_openapi(
    openapi_spec=spec,
    client=client,
    name="OData MCP",
    stateless_http=True,
    json_response=True,
)

# Health + root
@mcp.custom_route("/healthz", methods=["GET"])
async def healthz(_: Request) -> PlainTextResponse:
    return PlainTextResponse("OK")

@mcp.custom_route("/", methods=["GET"])
async def root(_: Request) -> JSONResponse:
    return JSONResponse({"status": "ok", "mcp_endpoint": "/mcp"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    host = os.environ.get("HOST", "0.0.0.0")
    mcp.run(transport="streamable-http", host=host, port=port, path="/mcp")
