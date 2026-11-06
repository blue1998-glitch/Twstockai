"""Pure evidence separation and conservative account observation sync.
No token, HTTP, secret loader, clock renewal or execution-enabling switch.
"""
import copy,hashlib,json
class EvidenceConflict(ValueError):pass
FACT_KEYS={"domain.name","domain.type","domain.home_region","domain.status","pilot.name","pilot.status"}
REQUIRED_REFERENCE_IDS={6654432698,6654557357,6654633563}

def validate_visual(doc):
    if doc.get("schema")!="qual-gate2-visual-ledger/0.1" or doc.get("source_kind")!="DIRECTOR_VERIFIED_OWNER_CONSOLE_VISUAL":raise EvidenceConflict("VISUAL_SOURCE_KIND")
    if not isinstance(doc.get("facts"),dict) or set(doc["facts"])!=FACT_KEYS:raise EvidenceConflict("VISUAL_MUST_NOT_ASSERT_API_OR_WIF")
    if {r.get("comment_id") for r in doc.get("references",[])}!=REQUIRED_REFERENCE_IDS:raise EvidenceConflict("SOURCE_REFERENCES")
    if any(r.get("codex_original_screenshot_read") is not False for r in doc["references"]):raise EvidenceConflict("ORIGINAL_SCREENSHOT_NOT_REOPENED")
    if any(not isinstance(v,str) or not v for v in doc["facts"].values()):raise EvidenceConflict("FACT_TYPES")
    return doc["facts"]

def sync_observations(account,doc):
    facts=validate_visual(doc);after=copy.deepcopy(account)
    values={"domain_kind":facts["domain.type"],"wif_feature_and_region":"Domain home region "+facts["domain.home_region"]+" confirmed by director-reviewed owner visual evidence; WIF rollout and quota UNKNOWN", "pilot_scope_and_iam":facts["pilot.name"]+" displayed "+facts["pilot.status"]+" in owner visual evidence; parent, independence, resource counts and IAM UNKNOWN"}
    for key,value in values.items():
        old=after["observations"].get(key)
        if old not in ("UNKNOWN",value):raise EvidenceConflict("PRESERVE_EXISTING_CONFLICT:"+key)
        after["observations"][key]=value
    for protected in ["schema","source","findings","captured_at","expires_at","config_binding","config"]:
        if after.get(protected)!=account.get(protected):raise EvidenceConflict("PROTECTED_RUNTIME_FIELD")
    return after

def assessment(account,visual,auth_observation):
    facts=validate_visual(visual)
    # Configured selectors/tool names alone never prove an authenticated session.
    authenticated=auth_observation.get("tenant_management_api_verified") is True
    return {"schema":"qual-gate2-assessment/0.1","status":"MANAGEMENT_API_EVIDENCE_REQUIRES_REVIEW" if authenticated else "BLOCKED_OWNER_AUTH",
            "execution_authorized":False,"known_visual_facts":copy.deepcopy(facts),
            "visual_evidence_is_management_api":False,"pilot_resource_counts":None,
            "wif_rollout":"UNKNOWN","remaining_quota":None,"minimum_iam_mapping":"UNKNOWN",
            "runtime_captured_at":account.get("captured_at"),"runtime_expires_at":account.get("expires_at"),
            "oracle_management_api_calls":auth_observation.get("management_api_calls",0),
            "next_read1_command_allowed":False}
