"""
AI Community Aid Navigator — Component Slice: Agent 1 & Agent 2
Contracts: docs/contracts/SHARED_CONTRACTS.md (v1.1)
Exposes unified handle(request: dict) -> dict entry point.
"""
from datetime import datetime, timezone
from typing import Any, Dict
from navigator.agents.agent_1_2.agent_1 import handle_agent_1
from navigator.agents.agent_1_2.agent_2 import handle_agent_2

def handle(request: Dict[str, Any]) -> Dict[str, Any]:
    role_id = request.get("role_id")
    if role_id == "agent_1":
        return handle_agent_1(request)
    elif role_id == "agent_2":
        return handle_agent_2(request)
    else:
        return {
            "request_id": request.get("request_id", "req-unknown"),
            "run_id": request.get("run_id", "run-unknown"),
            "case_id": request.get("case_id", "case-unknown"),
            "case_version": request.get("case_version", 1),
            "correlation_id": request.get("correlation_id", "corr-unknown"),
            "agent_id": str(role_id or "unassigned"),
            "schema_version": request.get("schema_version", "1.0"),
            "status": "failed",
            "result": {},
            "issues": [
                {
                    "code": "UNSUPPORTED_ROLE",
                    "severity": "critical",
                    "message": f"Component agent_1_2 cannot handle role_id: '{role_id}'. Expected 'agent_1' or 'agent_2'.",
                    "related_ref": None,
                }
            ],
            "clarification_requests": [],
            "evidence_refs": [],
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "is_mock": True,
        }
