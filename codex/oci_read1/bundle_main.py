"""Offline integrity and command check only. No OCI/GitHub network execution."""
import hashlib,json,sys,zipfile
from codex.oci_read1.protocol import parse_command

def verify_bundle():
    with zipfile.ZipFile(sys.argv[0]) as z:
        names=z.namelist()
        if len(names)!=len(set(names)) or z.testzip() is not None:
            raise ValueError("BUNDLE_MEMBERS_OR_CRC")
        manifest=json.loads(z.read("MANIFEST.json"))
        rows=manifest["files"]
        if set(names)!={row["path"] for row in rows}|{"MANIFEST.json"}:
            raise ValueError("BUNDLE_MANIFEST_SET")
        for row in rows:
            name=row["path"]
            if name.startswith("/") or ".." in name.split("/") or "\\" in name:
                raise ValueError("BUNDLE_PATH")
            raw=z.read(name)
            if len(raw)!=row["bytes"] or hashlib.sha256(raw).hexdigest()!=row["sha256"]:
                raise ValueError("BUNDLE_FINGERPRINT")
        return json.loads(z.read("stage.json"))

def main():
    try:
        stage=verify_bundle()
        mode=sys.argv[1:] or ["inspect"]
        if mode==["inspect"]:
            print(json.dumps(stage,sort_keys=True));return 0
        if mode==["check-command"]:
            parse_command(sys.stdin.buffer.read(257))
            print(json.dumps({"command_shape":"VALID", "authorized":False,
                "oracle_calls":0,"status":"BLOCKED_CREDENTIAL_ISOLATION"}));return 0
        print("READ1_NO_EXECUTION_OR_ACTIVATION_COMMAND");return 2
    except Exception:
        print("READ1_OFFLINE_CHECK_REFUSED");return 2
if __name__=="__main__":raise SystemExit(main())
