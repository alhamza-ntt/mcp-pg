
import httpx
from fastmcp import FastMCP
import json
import os
from fastapi import Request
from fastapi.responses import JSONResponse, PlainTextResponse
import uvicorn
import asyncio
from dotenv import load_dotenv


load_dotenv()

credusername = os.getenv("CREDUSERNAME")
credpass = os.getenv("CREDPASS")

if not credusername or not credpass:
    raise RuntimeError("Missing environment variables: CREDUSERNAME and/or CREDPASS")

client = httpx.AsyncClient(
    base_url="https://ntt-pi-dev.it-cpi001-rt.cfapps.eu10.hana.ondemand.com/http/df.nrw-sfd100-odata/zpp_workerassistant_srv/",
    auth=(credusername, credpass),
    headers={"Accept": "application/json"},
    verify=True,
)

with open("specs/odata_h2b.json", "r") as f:
    openapi_spec = f.read()
spec= json.loads(openapi_spec)


mcp = FastMCP.from_openapi(
    openapi_spec=spec,
    client=client,
    name="OData MCP",
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
    mcp.run(transport="streamable-http", host=host, port=port, path="/mcp")

import httpx
from fastmcp import FastMCP
import json
import os
from fastapi import Request
from fastapi.responses import JSONResponse, PlainTextResponse
import uvicorn
import asyncio
from dotenv import load_dotenv


load_dotenv()

credusername = os.getenv("CREDUSERNAME")
credpass = os.getenv("CREDPASS")

if not credusername or not credpass:
    raise RuntimeError("Missing environment variables: CREDUSERNAME and/or CREDPASS")

client = httpx.AsyncClient(
    base_url="https://ntt-pi-dev.it-cpi001-rt.cfapps.eu10.hana.ondemand.com/http/df.nrw-sfd100-odata/zpp_workerassistant_srv/",
    auth=(credusername, credpass),
    headers={"Accept": "application/json"},
    verify=True,
)

with open("specs/odata_h2b.json", "r") as f:
    openapi_spec = f.read()
spec= json.loads(openapi_spec)


mcp = FastMCP.from_openapi(
    openapi_spec=spec,
    client=client,
    name="OData MCP",
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
    mcp.run(transport="streamable-http", host=host, port=port, path="/mcp")
