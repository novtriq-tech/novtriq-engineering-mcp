"""
NOVTRIQ Engineering Intelligence MCP — public catalogue server.

This is the open, self-hostable face of the NOVTRIQ MCP. It advertises the full
tool catalogue (initialize / tools/list) so any MCP client or aggregator can
discover the 27 engineering tools, and it forwards actual execution (tools/call)
to the authoritative hosted endpoint. The tool implementations (the engineering
calculators) run on the hosted service, not in this repository.

  Hosted endpoint : https://api.novtriq.tech/mcp   (streamable-http, keyless free tier)
  Transport       : JSON-RPC 2.0 over HTTP
  Methods         : initialize, ping, tools/list, resources/list, prompts/list, tools/call

Run:
  pip install -r requirements.txt
  uvicorn server:app --host 0.0.0.0 --port 8080
"""
from __future__ import annotations

import json
import os
import pathlib

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

UPSTREAM = os.getenv("NOVTRIQ_MCP_UPSTREAM", "https://api.novtriq.tech/mcp")
PROTOCOL_VERSION = "2025-06-18"

_TOOLS = json.loads((pathlib.Path(__file__).parent / "tools.json").read_text(encoding="utf-8"))

SERVER_INFO = {
    "name": "novtriq-engineering",
    "version": "3.0.0",
    "description": "NOVTRIQ Engineering Intelligence MCP — %d tools for data centres, "
                   "building energy and carbon, UK building regulations, Eurocode structural "
                   "and cost, cyber and certification, and UAE compliance." % len(_TOOLS),
}

app = FastAPI(title="NOVTRIQ Engineering Intelligence MCP", version=SERVER_INFO["version"])


def _ok(result, _id):
    return {"jsonrpc": "2.0", "id": _id, "result": result}


def _err(code, message, _id):
    return {"jsonrpc": "2.0", "id": _id, "error": {"code": code, "message": message}}


@app.get("/")
def root():
    return {"service": "NOVTRIQ Engineering Intelligence MCP", "version": SERVER_INFO["version"],
            "mcp_endpoint": "/mcp", "hosted_endpoint": UPSTREAM, "tools": len(_TOOLS)}


@app.get("/health")
def health():
    return {"status": "ok", "service": "novtriq-mcp", "version": SERVER_INFO["version"], "tools": len(_TOOLS)}


@app.post("/mcp")
async def mcp(request: Request):
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(_err(-32700, "Invalid JSON body", None), status_code=400)

    _id = body.get("id") if isinstance(body, dict) else None
    if not isinstance(body, dict) or body.get("jsonrpc") != "2.0":
        return JSONResponse(_err(-32600, "jsonrpc field must be '2.0'", _id))

    method = body.get("method")

    if method == "initialize":
        return _ok({"protocolVersion": PROTOCOL_VERSION, "capabilities": {"tools": {}},
                    "serverInfo": SERVER_INFO}, _id)
    if method == "ping":
        return _ok({}, _id)
    if method == "tools/list":
        return _ok({"tools": _TOOLS}, _id)
    if method == "resources/list":
        return _ok({"resources": []}, _id)
    if method == "prompts/list":
        return _ok({"prompts": []}, _id)
    if method == "tools/call":
        # Execution is authoritative on the hosted service; forward the request as-is.
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                r = await client.post(UPSTREAM, json=body,
                                      headers={"Content-Type": "application/json"})
            return JSONResponse(r.json(), status_code=r.status_code)
        except Exception:
            return JSONResponse(_err(-32000,
                f"Tool execution is served by the hosted endpoint {UPSTREAM}, "
                f"which is currently unreachable from this instance.", _id))

    return JSONResponse(_err(-32601, f"Unknown method '{method}'", _id))
