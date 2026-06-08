"""
MCP HTTP client — talks to the MCP server (Layer 4) on behalf of agents (Layer 3).

Production version: agents/shared/mcp_client.py (~180 lines, with retry +
circuit breaker + adapter selection). This is the minimal version for the
workshop — direct httpx calls, no retry.
"""
from __future__ import annotations

import os
import uuid
from typing import Any

import httpx


class MCPClient:
    def __init__(self):
        self.base_url = os.getenv("MCP_URL", "http://mcp-server:8000").rstrip("/")
        self.api_key = os.getenv("MCP_API_KEY", "dev-key-123")
        self._client = httpx.AsyncClient(timeout=15.0)

    async def call_tool(self, tool_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Call /tools/<tool_name> with idempotency_key auto-generated."""
        payload = dict(payload)
        payload.setdefault("idempotency_key", str(uuid.uuid4()))
        url = f"{self.base_url}/tools/{tool_name}"
        resp = await self._client.post(
            url, json=payload, headers={"X-MCP-API-Key": self.api_key},
        )
        resp.raise_for_status()
        return resp.json()

    async def ospf_parser(self, device_id: str) -> dict[str, Any]:
        return await self.call_tool("ospf_parser", {"device_id": device_id})

    async def interface_parser(self, device_id: str) -> dict[str, Any]:
        return await self.call_tool("interface_parser", {"device_id": device_id})

    async def bgp_summary(self, device_id: str) -> dict[str, Any]:
        return await self.call_tool("bgp_summary", {"device_id": device_id})

    async def qos_parser(self, device_id: str) -> dict[str, Any]:
        return await self.call_tool("qos_parser", {"device_id": device_id})

    async def close(self):
        await self._client.aclose()
