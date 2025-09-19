import httpx
from fastmcp import FastMCP
import json
import os
from fastapi import Request
from fastapi.responses import JSONResponse, PlainTextResponse
import uvicorn
import asyncio
from dotenv import load_dotenv
from typing import List, Dict, Any
from search import search_in_index  

load_dotenv()

odata_username = os.getenv("CREDUSERNAME")  
odata_password = os.getenv("CREDPASS")
odata_base_url = "https://ntt-pi-dev.it-cpi001-rt.cfapps.eu10.hana.ondemand.com/http/df.nrw-sfd100-odata/zpp_workerassistant_srv/"

if not odata_username or not odata_password:
    raise RuntimeError("Missing OData credentials: ODATA_USERNAME and/or ODATA_PASSWORD")


odata_client = httpx.AsyncClient(
    base_url=odata_base_url,
    auth=(odata_username, odata_password),
    headers={"Accept": "application/json"},
    verify=True,
)

with open("specs/odata_h2b.json", "r") as f:
    openapi_spec = f.read()
spec = json.loads(openapi_spec)

mcp = FastMCP.from_openapi(
    openapi_spec=spec,
    client=odata_client,  
    name="Worker Assistant MCP",
    stateless_http=True,          
    json_response=True            
)


@mcp.tool()
async def search_knowledge_base(
    query: str,
    top_k_contexts: int = 5
) -> Dict[str, Any]:
    """
    Search documented procedures, policies, training materials, and company guidelines using Azure Cognitive Search.
    Uses hybrid search (keyword + vector) with semantic reranking for best results.
    Use for historical knowledge, best practices, safety procedures, and documented processes.
    """
    try:
        loop = asyncio.get_event_loop()
        contexts = await loop.run_in_executor(None, search_in_index, query, top_k_contexts)
        
        return {
            "query": query,
            "results_count": len(contexts),
            "documents": contexts,
            "metadata": {
                "search_type": "hybrid_semantic",
                "top_k": top_k_contexts,
                "has_images": sum(1 for ctx in contexts if ctx.get("has_image", False))
            }
        }
        
    except Exception as e:
        return {
            "error": f"Azure Cognitive Search failed: {str(e)}",
            "query": query,
            "results_count": 0,
            "documents": []
        }

@mcp.tool()
async def search_all_sources(
    query: str,
    include_odata: bool = True,
    include_knowledge: bool = True,
    odata_filter: str = "",
    top_k_contexts: int = 3
) -> Dict[str, Any]:
    """
    Search across multiple data sources simultaneously.
    Use when you need comprehensive information from both live operational data and documentation.
    """
    results = {
        "query": query,
        "sources_searched": [],
        "odata_results": None,
        "knowledge_results": None,
        "combined_summary": ""
    }
    
    # Search OData if requested
    if include_odata:
        try:
            # Build OData query - simplified example
            odata_endpoint = "WorkerGenericSet"
            params = {
                "$format": "json",
                "$top": "5",
                "$expand": "WorkerGenericFieldlist"
            }
            if odata_filter:
                params["$filter"] = odata_filter
            
            odata_response = await odata_client.get(odata_endpoint, params=params)
            if odata_response.status_code == 200:
                results["odata_results"] = odata_response.json()
                results["sources_searched"].append("odata")
        except Exception as e:
            results["odata_results"] = {"error": str(e)}
    
    # Search Knowledge Base if requested  
    if include_knowledge:
        knowledge_result = await search_knowledge_base(query, top_k_contexts)
        results["knowledge_results"] = knowledge_result
        if not knowledge_result.get("error"):
            results["sources_searched"].append("knowledge_base")
    
    # Add summary
    sources_found = len(results["sources_searched"])
    total_docs = 0
    if results.get("knowledge_results"):
        total_docs += results["knowledge_results"].get("results_count", 0)
    if results.get("odata_results") and not results["odata_results"].get("error"):
        total_docs += len(results["odata_results"].get("d", {}).get("results", []))
    
    results["combined_summary"] = f"Searched {sources_found} sources, found {total_docs} relevant items for: {query}"
    
    return results

# Health check and root endpoints
@mcp.custom_route("/healthz", methods=["GET"])
async def healthz(_: Request) -> PlainTextResponse:
    return PlainTextResponse("OK")

@mcp.custom_route("/", methods=["GET"])
async def root(_: Request) -> JSONResponse:
    return JSONResponse({
        "status": "ok", 
        "mcp_endpoint": "/mcp",
        "data_sources": ["odata", "azure_cognitive_search"],
        "tools": ["query_worker_generic_set", "get_worker_generic_item", "search_knowledge_base", "search_all_sources"]
    })

async def cleanup():
    await odata_client.aclose()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    host = os.environ.get("HOST", "0.0.0.0")
    try:
        mcp.run(transport="streamable-http", host=host, port=port, path="/mcp")
    finally:
        asyncio.run(cleanup())