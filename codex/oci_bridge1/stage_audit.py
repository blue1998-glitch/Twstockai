"""No-secret private delivery audit. No GitHub/OCI calls or execution switch."""
import hashlib,json,re,sys
from pathlib import Path
from .bridge import Refused,strict
FILES={'__init__.py','bridge.py','receiver.py','stage_audit.py','control-policy.json'}
def audit(root,expected_manifest_sha):
 root=Path(root)
 if any(p.is_symlink() for p in (root,*root.parents)):raise Refused('STAGE_SYMLINK')
 if not re.fullmatch('[a-f0-9]{64}',expected_manifest_sha):raise Refused('MANIFEST_PIN')
 manifest=root/'MANIFEST.json'
 if manifest.is_symlink() or manifest.stat().st_size>4096:raise Refused('MANIFEST_FILE')
 raw=manifest.read_bytes()
 if hashlib.sha256(raw).hexdigest()!=expected_manifest_sha:raise Refused('MANIFEST_PIN')
 doc=strict(raw);rows=doc.get('files')
 if doc.get('schema')!='oci-private-review/0.1' or not isinstance(rows,list) or len(rows)!=len(FILES) or {r.get('path') for r in rows}!=FILES:raise Refused('MANIFEST_SET')
 for row in rows:
  file=root/row['path']
  if file.is_symlink() or not file.is_file() or file.stat().st_size>131072:raise Refused('STAGE_FILE')
  raw=file.read_bytes()
  if len(raw)!=row['bytes'] or hashlib.sha256(raw).hexdigest()!=row['sha256']:raise Refused('STAGE_SHA')
 policy=strict((root/'control-policy.json').read_bytes())
 fields={'schema','repository','repository_id','actor_id','app_id','installation_id','issue_number','workflow_sha','workflow_ref','billing_status','execution_state','pilot_configured'}
 if set(policy)!=fields or policy['schema']!='oci-private-staging/0.1':raise Refused('POLICY_FIELDS')
 if policy['repository']!='blue1998-glitch/Twstockai-oci-bridge-private' or policy['repository_id']!=1446437252 or policy['actor_id']!=319797247 or policy['app_id']!=1144995 or policy['issue_number']!=1:raise Refused('PRIVATE_BINDING')
 if type(policy['installation_id']) is not int or policy['installation_id']<=0:raise Refused('INSTALLATION_BINDING')
 if policy['workflow_sha'] is not None or policy['execution_state']!='STAGED_NOT_ENABLED' or policy['billing_status']!='UNVERIFIED' or policy['pilot_configured'] is not False:raise Refused('NO_ACTIVATION_BY_STAGING')
 return {'status':'NOT_CONNECTED','private_bundle_verified':True,'files':len(rows),'actions_started':0,'oracle_queries':0,'billing':'UNVERIFIED','workflow':'NOT_ENABLED'}
def main():
 try:print(json.dumps(audit(Path(__file__).parent,sys.argv[1])))
 except Exception:print(json.dumps({'status':'NOT_CONNECTED','private_bundle_verified':False}));return 2
 return 0
if __name__=='__main__':raise SystemExit(main())
