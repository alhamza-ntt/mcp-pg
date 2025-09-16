# combined_mcp_app.py
import os
import json
import asyncio
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from contextlib import asynccontextmanager
from fastmcp import FastMCP
import uvicorn

# ---- build sub-apps (async because of import_server) ----
async def build_apps():
    load_dotenv()

    # -------- tools1: SuccessFactors ClockInClockOut --------
    sf_headers = {
        "APIKey": os.getenv("SAP_APIKey"),
        "Accept": "application/json",
        "DataServiceVersion": "2.0",
    }
    tools1_client = httpx.AsyncClient(
        base_url="https://sandbox.api.sap.com/successfactors/odata/v2",
        headers=sf_headers,
        timeout=30.0,
    )

    with open("specs/simplified_payroll.json", "r", encoding="utf-8") as f:
        tools1_spec = json.load(f)

    tools1_mcp = FastMCP.from_openapi(
        openapi_spec=tools1_spec,
        client=tools1_client,
        name="clockinclockout",
        stateless_http=True,
        json_response=True,
    )
    tools1_app = tools1_mcp.http_app(path="/mcp")  # -> /tools1/mcp when mounted

    # -------- tools2: CPI OData Worker Assistant --------
    creduser = os.getenv("CREDUSERNAME")
    credpass = os.getenv("CREDPASS")
    if not creduser or not credpass:
        raise RuntimeError("Missing env vars: CREDUSERNAME and/or CREDPASS")

    odata_client = httpx.AsyncClient(
        base_url=("https://ntt-pi-dev.it-cpi001-rt.cfapps.eu10.hana.ondemand.com/"
                  "http/df.nrw-sfd100-odata/zpp_workerassistant_srv/"),
        auth=(creduser, credpass),
        headers={"Accept": "application/json"},
        timeout=30.0,
        verify=True,
    )

    with open("specs/odata_h2b.json", "r", encoding="utf-8") as f:
        tools2_spec = json.load(f)

    tools2_mcp = FastMCP.from_openapi(
        openapi_spec=tools2_spec,
        client=odata_client,
        name="OData MCP",
        stateless_http=True,
        json_response=True,
    )
    tools2_app = tools2_mcp.http_app(path="/mcp")  # -> /tools2/mcp when mounted

    # -------- combined endpoint (both, with prefixes) --------
    combined = FastMCP(name="combined")
    await combined.import_server(tools1_mcp, prefix="tools1")
    await combined.import_server(tools2_mcp, prefix="tools2")
    combined_app = combined.http_app(path="/mcp")  # -> /mcp when mounted at "/"

    return tools1_app, tools2_app, combined_app


def make_parent_app(tools1_app, tools2_app, combined_app):
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # ensure sub-app startup/shutdown are called
        async with tools1_app.lifespan(app):
            async with tools2_app.lifespan(app):
                async with combined_app.lifespan(app):
                    yield

    app = FastAPI(lifespan=lifespan)

    # simple health/root on the parent
    @app.get("/healthz")
    async def healthz(_: Request):
        return PlainTextResponse("OK")

    @app.get("/")
    async def root(_: Request):
        return JSONResponse({
            "status": "ok",
            "endpoints": {
                "tools1_only": "/tools1/mcp",
                "tools2_only": "/tools2/mcp",
                "both_combined": "/mcp",
            }
        })

    # mount sub-apps
    app.mount("/tools1", tools1_app)   # -> http://host:port/tools1/mcp
    app.mount("/tools2", tools2_app)   # -> http://host:port/tools2/mcp
    app.mount("/", combined_app)       # -> http://host:port/mcp  (both)

    return app


if __name__ == "__main__":
    tools1_app, tools2_app, combined_app = asyncio.run(build_apps())
    app = make_parent_app(tools1_app, tools2_app, combined_app)

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host=host, port=port)


