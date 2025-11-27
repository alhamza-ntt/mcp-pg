import os
import json
import asyncio
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from fastmcp import FastMCP
import uvicorn


async def build_single_mcp(name, base_url, spec_file, headers, auth):
    client = httpx.AsyncClient(
        base_url=base_url,
        headers=headers,
        auth=auth,
        timeout=30.0,
        verify=True,
    )

    with open(spec_file, "r") as f:
        spec = json.load(f)

    mcp = FastMCP.from_openapi(
        openapi_spec=spec,
        client=client,
        name=name,
        stateless_http=True,
        json_response=True,
    )

    return mcp


async def build_all_mcp():
    load_dotenv()

    sap_user = os.getenv("general_s4hana_user")
    sap_pass = os.getenv("general_s4hana_password")
    auth = (sap_user, sap_pass)

    headers = {
        "Accept": "application/json",
        "DataServiceVersion": "2.0",
    }

    purchase_mcp = await build_single_mcp(
        name="purchase_req_MCP",
        base_url=os.getenv("purchase_req_base_url"),
        spec_file="specs/mini_purchase_req.json",
        headers=headers,
        auth=auth,
    )
    purchase_app = purchase_mcp.http_app(path="/mcp")

    sales_mcp = await build_single_mcp(
        name="sales_order_MCP",
        base_url=os.getenv("sales_order_base_url"),
        spec_file="specs/API_SALES_ORDER_SRV_reduced.json",
        headers=headers,
        auth=auth,
    )
    sales_app = sales_mcp.http_app(path="/mcp")

    combined = FastMCP(name="combined")
    await combined.import_server(purchase_mcp, prefix="purchase")
    await combined.import_server(sales_mcp, prefix="sales")
    combined_app = combined.http_app(path="/mcp")

    return purchase_app, sales_app, combined_app


def make_parent_app(purchase_app, sales_app, combined_app):
    @asynccontextmanager
    async def lifespan(app):
        async with purchase_app.lifespan(app):
            async with sales_app.lifespan(app):
                async with combined_app.lifespan(app):
                    yield

    app = FastAPI(lifespan=lifespan)

    @app.get("/healthz")
    async def health(_: Request):
        return PlainTextResponse("OK")

    @app.get("/")
    async def root(_: Request):
        return JSONResponse({
            "status": "ok",
            "endpoints": {
                "purchase": "/purchase/mcp",
                "sales": "/sales/mcp",
                "combined": "/combined/mcp",
            }
        })

    app.mount("/purchase", purchase_app)
    app.mount("/sales", sales_app)
    app.mount("/combined", combined_app)

    return app


if __name__ == "__main__":
    purchase_app, sales_app, combined_app = asyncio.run(build_all_mcp())
    app = make_parent_app(purchase_app, sales_app, combined_app)

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host=host, port=port)
