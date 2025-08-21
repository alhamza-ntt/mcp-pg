import httpx
from fastmcp import FastMCP
import json
import os
from fastapi import Request
from fastapi.responses import JSONResponse, PlainTextResponse
import uvicorn
from fastapi.responses import HTMLResponse  # add to your imports

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


with open("payrol_converted.json", "r") as f:
    spec = json.load(f)


mcp = FastMCP.from_openapi(
    openapi_spec=spec,
    client=client,
    name="SAP MCP",
    stateless_http=True,          # << disable MCP sessions
    json_response=True            # << simpler responses for some clients
)

@mcp.custom_route("/healthz", methods=["GET"])
async def healthz(_: Request) -> PlainTextResponse:
    return PlainTextResponse("OK")

@mcp.custom_route("/", methods=["GET"])
async def root(_: Request) -> JSONResponse:
    return JSONResponse({"status": "ok", "mcp_endpoint": "/mcp"})


KEEP = [
    "Get_entities_from_EmployeeTimeSheet",
    "Get_entity_from_EmployeeTimeSheet_by_key",
    "Get_entities_from_EmployeeTimeSheetEntry",
    "Get_entity_from_EmployeeTimeSheetEntry_by_key",
]

# The list that will be shown in the UI (you can add/remove here)
ALL_TOOLS = KEEP[:]  # start with the same set; extend later if you want

def makecall(q: str, allowed_tools: list[str] | None = None):
    if not allowed_tools:
        allowed_tools = KEEP

    resp = clientopenai.responses.create(
        model="gpt-4.1",
        temperature=0,
        instructions=rules,  # your existing guardrails string
        tools=[{
            "type": "mcp",
            "server_label": "PayrollTimeSheet",
            "server_url": "https://pg-aib-afgmech7ccdqdedh.canadacentral-01.azurewebsites.net/mcp",
            "require_approval": "never",
            "allowed_tools": allowed_tools,
        }],
        input=q
    )

    # Make usage JSON-safe
    usage = getattr(resp, "usage", None)
    usage_json = None
    if usage:
        usage_json = {
            "input_tokens": getattr(usage, "input_tokens", None),
            "output_tokens": getattr(usage, "output_tokens", None),
            "total_tokens": getattr(usage, "total_tokens", None),
        }

    return usage_json, getattr(resp, "output_text", "")


@mcp.custom_route("/tools", methods=["GET"])
async def list_tools(_: Request) -> JSONResponse:
    # Simple static allow-list for now
    return JSONResponse({"tools": ALL_TOOLS})

@mcp.custom_route("/call", methods=["POST"])
async def call_endpoint(req: Request) -> JSONResponse:
    data = await req.json()
    query = (data.get("query") or "").strip()
    tools = data.get("tools") or []

    if not query:
        return JSONResponse({"error": "query is required"}, status_code=400)

    usage, text = makecall(query, tools)
    return JSONResponse({"usage": usage, "output_text": text})

@mcp.custom_route("/ui", methods=["GET"])
async def ui(_: Request) -> HTMLResponse:
    html = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Tool Picker</title>
  <style>
    body { font-family: system-ui, sans-serif; margin: 24px; }
    .row { margin-bottom: 12px; }
    select { width: 420px; height: 160px; }
    textarea, input[type=text] { width: 420px; }
    button { padding: 8px 14px; cursor: pointer; }
    pre { background: #f6f8fa; padding: 12px; overflow: auto; }
  </style>
</head>
<body>
  <h2>Pick tools, type a prompt, and send</h2>

  <div class="row">
    <label><strong>Tools (multi-select):</strong></label><br/>
    <select id="tools" multiple></select><br/>
    <small>Hold Ctrl/Cmd or Shift to select multiple.</small>
  </div>

  <div class="row">
    <label for="query"><strong>Query:</strong></label><br/>
    <textarea id="query" rows="4" placeholder="e.g. Get entity 0001623e1b284cc8b0b8be7e138f535f"></textarea>
  </div>

  <div class="row">
    <button id="send">Send</button>
  </div>

  <div class="row">
    <h3>Response</h3>
    <div><strong>output_text</strong></div>
    <pre id="out"></pre>
    <div><strong>usage</strong></div>
    <pre id="usage"></pre>
  </div>

<script>
async function loadTools() {
  const res = await fetch('/tools');
  const data = await res.json();
  const sel = document.getElementById('tools');
  sel.innerHTML = '';
  (data.tools || []).forEach(t => {
    const opt = document.createElement('option');
    opt.value = t;
    opt.textContent = t;
    sel.appendChild(opt);
  });
}

function getSelectedTools() {
  const sel = document.getElementById('tools');
  return Array.from(sel.selectedOptions).map(o => o.value);
}

async function sendQuery() {
  const query = document.getElementById('query').value;
  const tools = getSelectedTools();

  const res = await fetch('/call', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({ query, tools })
  });

  const data = await res.json();
  document.getElementById('out').textContent = data.output_text || JSON.stringify(data, null, 2);
  document.getElementById('usage').textContent = data.usage ? JSON.stringify(data.usage, null, 2) : '—';
}

document.getElementById('send').addEventListener('click', sendQuery);
loadTools();
</script>
</body>
</html>
"""
    return HTMLResponse(html)



if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    host = os.environ.get("HOST", "0.0.0.0")
    # Be explicit about the modern transport and path
    mcp.run(transport="streamable-http", host=host, port=port, path="/mcp")
