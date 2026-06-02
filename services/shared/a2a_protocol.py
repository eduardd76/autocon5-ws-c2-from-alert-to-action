"""
A2A protocol — minimal version for the workshop.

Production lives in agents/shared/a2a_protocol.py (~250 lines). This
strip-down keeps the same message types + Redis-list semantics so the
attendee mental model matches the real system.
"""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any

import redis.asyncio as redis


class MessageType(str, Enum):
    TASK_DELEGATION = "task_delegation"   # Team Leader -> Specialist
    TASK_RESPONSE = "task_response"       # Specialist -> Team Leader
    STATUS_UPDATE = "status_update"
    ESCALATION = "escalation"


class AgentRole(str, Enum):
    TEAM_LEADER = "team_leader"
    STABILITY_SPECIALIST = "stability_specialist"
    TROUBLESHOOTING_SPECIALIST = "troubleshooting_specialist"
    SECURITY_SPECIALIST = "security_specialist"
    VIRTUAL_ARCHITECT = "virtual_architect"
    # Lab 3: attendees add their role here.
    YOUR_SPECIALIST = "your_specialist"


@dataclass
class A2AMessage:
    message_type: MessageType
    from_agent: AgentRole
    to_agent: AgentRole
    task_id: str
    payload: dict[str, Any]
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_json(self) -> str:
        d = asdict(self)
        d["message_type"] = self.message_type.value
        d["from_agent"] = self.from_agent.value
        d["to_agent"] = self.to_agent.value
        return json.dumps(d)

    @classmethod
    def from_json(cls, s: str) -> "A2AMessage":
        d = json.loads(s)
        return cls(
            message_type=MessageType(d["message_type"]),
            from_agent=AgentRole(d["from_agent"]),
            to_agent=AgentRole(d["to_agent"]),
            task_id=d["task_id"],
            payload=d["payload"],
            correlation_id=d.get("correlation_id", str(uuid.uuid4())),
            message_id=d.get("message_id", str(uuid.uuid4())),
            timestamp=d.get("timestamp", datetime.now(timezone.utc).isoformat()),
        )


class A2AChannel:
    """Thin wrapper around Redis lists. One inbox per agent role."""

    def __init__(self, redis_client: redis.Redis, role: AgentRole):
        self.redis = redis_client
        self.role = role
        self.inbox = f"a2a_{role.value}_inbox"

    async def send(self, msg: A2AMessage) -> None:
        target = f"a2a_{msg.to_agent.value}_inbox"
        await self.redis.lpush(target, msg.to_json())
        print(f"[A2A] {msg.from_agent.value} -> {msg.to_agent.value}: {msg.message_type.value}")

    async def receive(self, timeout: int = 5) -> A2AMessage | None:
        result = await self.redis.brpop(self.inbox, timeout=timeout)
        if result is None:
            return None
        _, raw = result
        return A2AMessage.from_json(raw)

    async def send_delegation(
        self, to_agent: AgentRole, task_id: str, payload: dict[str, Any]
    ) -> None:
        msg = A2AMessage(
            message_type=MessageType.TASK_DELEGATION,
            from_agent=self.role,
            to_agent=to_agent,
            task_id=task_id,
            payload=payload,
        )
        await self.send(msg)

    async def send_response(
        self, to_agent: AgentRole, task_id: str, result: dict[str, Any],
        correlation_id: str | None = None,
    ) -> None:
        msg = A2AMessage(
            message_type=MessageType.TASK_RESPONSE,
            from_agent=self.role,
            to_agent=to_agent,
            task_id=task_id,
            payload={"result": result},
            correlation_id=correlation_id or str(uuid.uuid4()),
        )
        await self.send(msg)
