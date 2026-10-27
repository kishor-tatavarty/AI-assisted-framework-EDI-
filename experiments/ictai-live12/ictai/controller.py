"""ICTAI minimal evidence-driven layer controller. No LLM or RCA claim yet."""
from dataclasses import dataclass, field
from typing import Callable

LAYER_TOOLS = {
    "source": ("inspect_manifest", "check_object_inventory", "check_upstream_health"),
    "validation": ("inspect_schema_contract", "inspect_observed_schema", "inspect_invalid_records"),
    "pipeline": ("inspect_task_execution", "read_run_events"),
    "lineage": ("query_lineage",),
    "impact": ("query_lineage", "inspect_output_measurements"),
}

@dataclass
class Investigation:
    incident_id: str
    evidence: list = field(default_factory=list)
    visited: list = field(default_factory=list)
    audit: list = field(default_factory=list)
    status: str = "OPEN"

def investigate(incident_id: str, available_tools: dict[str, Callable],
                priority: tuple[str, ...] = ("source", "validation", "pipeline", "lineage", "impact"),
                max_calls: int = 4) -> Investigation:
    """Deterministic bounded controller; tool results are evidence, not RCA conclusions."""
    if max_calls < 1: raise ValueError("max_calls must be positive")
    ctx = Investigation(incident_id)
    calls = 0
    for layer in priority:
        if layer not in LAYER_TOOLS: raise ValueError(f"unknown layer: {layer}")
        ctx.visited.append(layer)
        for tool_name in LAYER_TOOLS[layer]:
            if tool_name not in available_tools: continue
            if calls >= max_calls:
                ctx.status = "BUDGET_EXHAUSTED"
                return ctx
            calls += 1
            try:
                result = available_tools[tool_name]()
                ctx.evidence.append({"layer":layer,"tool":tool_name,"result":result})
                ctx.audit.append({"step":calls,"layer":layer,"tool":tool_name,"outcome":"ok"})
            except Exception as exc:
                ctx.audit.append({"step":calls,"layer":layer,"tool":tool_name,"outcome":"error","error_type":type(exc).__name__})
    ctx.status = "EVIDENCE_COLLECTED" if ctx.evidence else "INSUFFICIENT_EVIDENCE"
    return ctx


# Phase 2: context-aware layer selection. Existing investigate() remains a fixed-order baseline.
SIGNAL_LAYERS = {
    "missing_file": ("source", "pipeline", "validation", "lineage", "impact"),
    "schema_drift": ("validation", "source", "pipeline", "lineage", "impact"),
    "pipeline_failure": ("pipeline", "source", "validation", "lineage", "impact"),
    "dependency_failure": ("pipeline", "source", "lineage", "validation", "impact"),
    "data_quality": ("validation", "source", "pipeline", "lineage", "impact"),
    "freshness": ("source", "pipeline", "validation", "lineage", "impact"),
}

def select_next_layer(signal: str, visited: list[str], available_tools: dict,
                      evidence: list | None = None) -> str | None:
    """Choose an unvisited layer with an available tool; no ground-truth access."""
    if signal not in SIGNAL_LAYERS:
        raise ValueError(f"unknown incident signal: {signal}")
    order = list(SIGNAL_LAYERS[signal])
    # Observed tool evidence can redirect the next layer.
    for item in evidence or []:
        result = item.get("result")
        if not isinstance(result, dict):
            continue
        if result.get("schema_mismatch") is True or result.get("contract_violated") is True:
            order = ["validation"] + [x for x in order if x != "validation"]
        elif result.get("task_failed") is True:
            order = ["pipeline"] + [x for x in order if x != "pipeline"]
        elif result.get("upstream_unavailable") is True:
            order = ["source"] + [x for x in order if x != "source"]
    return next((layer for layer in order
                 if layer not in visited
                 and any(t in available_tools for t in LAYER_TOOLS[layer])), None)

def investigate_dynamic(incident_id: str, signal: str, available_tools: dict[str, Callable],
                        max_calls: int = 4, max_layers: int = 5) -> Investigation:
    """Bounded dynamic evidence collection; no RCA or calibrated confidence claim."""
    if max_calls < 1 or max_layers < 1:
        raise ValueError("max_calls and max_layers must be positive")
    ctx = Investigation(incident_id)
    calls = 0
    while len(ctx.visited) < max_layers:
        layer = select_next_layer(signal, ctx.visited, available_tools, ctx.evidence)
        if layer is None:
            break
        ctx.visited.append(layer)
        ctx.audit.append({"event": "layer_selected", "layer": layer,
                          "signal": signal, "visited_before": ctx.visited[:-1]})
        for tool_name in LAYER_TOOLS[layer]:
            if tool_name not in available_tools:
                continue
            if calls >= max_calls:
                ctx.status = "BUDGET_EXHAUSTED"
                return ctx
            calls += 1
            try:
                result = available_tools[tool_name]()
                ctx.evidence.append({"layer": layer, "tool": tool_name, "result": result})
                ctx.audit.append({"step": calls, "layer": layer, "tool": tool_name, "outcome": "ok"})
            except Exception as exc:
                ctx.audit.append({"step": calls, "layer": layer, "tool": tool_name,
                                  "outcome": "error", "error_type": type(exc).__name__})
    ctx.status = "EVIDENCE_COLLECTED" if ctx.evidence else "INSUFFICIENT_EVIDENCE"
    return ctx
