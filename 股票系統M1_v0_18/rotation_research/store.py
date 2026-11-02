"""External immutable result store. Reads never call the replay engine."""
import json, os, re
from pathlib import Path

class Journal:
    def __init__(self,root): self.root=Path(root)
    def path(self,key):
        if not re.fullmatch('[A-Za-z0-9_-]{1,120}',key): raise ValueError('Invalid identity')
        return self.root/(key+'.json')
    def read(self,key):
        p=self.path(key)
        if p.is_symlink(): raise ValueError('Refuse symlink')
        from rotation_research.artifact_codec import read_bytes
        result=json.loads(read_bytes(p))
        if result['id'] != key or result['schema'] != 'rotation-record/0.1': raise ValueError('Corrupt identity/schema')
        return result
    def save(self,key,value,*,compact=False,storage_root=None,bases=()):
        p=self.path(key);self.root.mkdir(parents=True,exist_ok=True)
        record={'schema':'rotation-record/0.1','id':key,'value':value}
        body=(json.dumps(record,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
        from rotation_research import artifact_codec as codec
        if compact:
            if storage_root is None:raise ValueError('Explicit private storage root required')
            codec.publish_interned(p,body,root=storage_root,bases=bases,format='journal')
            return self.read(key)
        if codec.sidecar(p).exists():
            if codec.read_bytes(p)!=body:raise ValueError('Identity conflict: existing compact record preserved')
            return self.read(key)
        try: fd=os.open(p,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
        except FileExistsError:
            if p.is_symlink() or p.read_bytes()!=body: raise ValueError('Identity conflict: existing file preserved')
            return self.read(key)
        with os.fdopen(fd,'wb') as f: f.write(body);f.flush();os.fsync(f.fileno())
        # Interrupted partial files are preserved and rejected on read, not silently repaired.
        return self.read(key)
