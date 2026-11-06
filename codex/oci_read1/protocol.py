"""Pure command/result projection. NOT an authorizer or an active receiver.
Use only after a separately approved native receiver, durable nonce and OCI
identity boundary. This module never loads credentials or creates SDK clients.
"""
import re
from codex.oci_bridge1.bridge import Refused, strict, sanitize
SCHEMA = "oci-read/0.1"
OPERATION = "list_pilot_compartment_resources"
VERSION = "M-OCI-READ1/0.1-STAGED"

def parse_command(raw):
    if not isinstance(raw, bytes) or len(raw) > 256:
        raise Refused("READ1_COMMAND_BOUND")
    value = strict(raw)
    if not isinstance(value, dict) or set(value) != {"schema", "operation"}:
        raise Refused("READ1_COMMAND_FIELDS")
    if value["schema"] != SCHEMA or value["operation"] != OPERATION:
        raise Refused("READ1_COMMAND_OPERATION")
    return value

def project_result(result, *, request_comment_id, run_id, workflow_sha, adapter_sha256):
    # This function does NOT prove a caller, native run or actual OCI execution.
    # Never publish its output as an attestation without that separate boundary.
    if any(type(v) is not int or v <= 0 for v in (request_comment_id, run_id)):
        raise Refused("READ1_RECEIPT_ID")
    if not isinstance(workflow_sha, str) or not re.fullmatch("[a-f0-9]{40}", workflow_sha):
        raise Refused("READ1_RECEIPT_VERSION")
    if not isinstance(adapter_sha256, str) or not re.fullmatch("[a-f0-9]{64}", adapter_sha256):
        raise Refused("READ1_ADAPTER_PIN")
    safe = sanitize(result)
    if safe["reason"] != "PILOT_SCOPE_ONLY":
        raise Refused("READ1_PILOT_OPERATION_ONLY")
    return {"schema": "oci-read-result-projection/0.1", "version": VERSION,
            "operation": OPERATION, "request_comment_id": request_comment_id,
            "run_id": run_id, "workflow_sha": workflow_sha,
            "adapter_sha256": adapter_sha256, "result": safe,
            "attestation": "NOT_ATTESTED_BY_PROJECTION"}
