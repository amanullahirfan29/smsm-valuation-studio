"""Portable source+assumption snapshot for user sessions. No network or persistence."""
from __future__ import annotations
import json
from copy import deepcopy

SCHEMA = "SMSM_VALUATION_STUDIO_INPUTS_V1"
MAX_BYTES=1_000_000

def export_input_snapshot(data:dict)->bytes:
    payload={"format":SCHEMA,"payload":data}
    return json.dumps(payload,ensure_ascii=False,indent=2,allow_nan=False).encode("utf-8")

def import_input_snapshot(raw:bytes)->dict:
    if not raw or len(raw)>MAX_BYTES:
        raise ValueError("Saved input must be valid JSON no larger than 1MB")
    obj=json.loads(raw.decode("utf-8"))
    if not isinstance(obj,dict) or obj.get("format")!=SCHEMA or not isinstance(obj.get("payload"),dict):
        raise ValueError("Unsupported or incorrect saved input format")
    d=deepcopy(obj["payload"])
    for key in ("historical","interim","scenarios","bridge","cost_of_capital","peers","valuation_date"):
        if key not in d:raise ValueError(f"Saved inputs missing {key}")
    if d["valuation_date"]!="2026-10-23":raise ValueError("Saved inputs do not match the approved valuation-date cutoff")
    return d
