"""
stdio_server.py — NOVTRIQ Engineering Intelligence MCP over stdio.

Companion to server.py (HTTP). This variant speaks the MCP stdio transport, which
is what mcp-proxy / Glama's build checker wrap. It advertises the same 27 tool
definitions from tools.json (served locally, so initialize and tools/list work with
no network) and forwards tools/call to the authoritative hosted endpoint. The
engineering calculators stay on the hosted service.

Run:
  pip install -r requirements.txt
  python -u stdio_server.py
"""
from __future__ import annotations

import asyncio
import json
import os
import pathlib

import httpx
import mcp.types as types
from mcp.server import Server
from mcp.server.stdio import stdio_server

UPSTREAM = os.getenv("NOVTRIQ_MCP_UPSTREAM", "https://api.novtriq.tech/mcp")
_TOOLS = json.loads((pathlib.Path(__file__).parent / "tools.json").read_text(encoding="utf-8"))

app = Server("novtriq-engineering")


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [types.Tool(name=t["name"], description=t.get("description", ""),
                       inputSchema=t.get("inputSchema", {"type": "object"})) for t in _TOOLS]


@app.call_tool()
async def call_tool(name: str, arguments: dict | None) -> list[types.TextContent]:
    """Execution is authoritative on the hosted service; forward the call as JSON-RPC."""
    payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
               "params": {"name": name, "arguments": arguments or {}}}
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(UPSTREAM, json=payload,
                                  headers={"Content-Type": "application/json"})
        data = r.json()
    except Exception as exc:
        return [types.TextContent(type="text",
                text=f"Tool execution is served by the hosted endpoint {UPSTREAM}, "
                     f"which is currently unreachable ({exc}).")]
    result = data.get("result") or {}
    content = result.get("content")
    if isinstance(content, list) and content:
        out = [types.TextContent(type="text", text=c.get("text", "")) for c in content
               if isinstance(c, dict) and c.get("type") == "text" and c.get("text")]
        if out:
            return out
    if "error" in data:
        return [types.TextContent(type="text", text=json.dumps(data["error"]))]
    return [types.TextContent(type="text", text=json.dumps(result))]


async def main() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
