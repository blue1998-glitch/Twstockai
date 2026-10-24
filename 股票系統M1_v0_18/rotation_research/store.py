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
        result=json.loads(p.read_text())
        if result['id'] != key or result['schema'] != 'rotation-record/0.1': raise ValueError('Corrupt identity/schema')
        return result
    def save(self,key,value):
        p=self.path(key);self.root.mkdir(parents=True,exist_ok=True)
        record={'schema':'rotation-record/0.1','id':key,'value':value}
        body=(json.dumps(record,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
        try: fd=os.open(p,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
        except FileExistsError:
            if p.is_symlink() or p.read_bytes()!=body: raise ValueError('Identity conflict: existing file preserved')
            return self.read(key)
        with os.fdopen(fd,'wb') as f: f.write(body);f.flush();os.fsync(f.fileno())
        # Interrupted partial files are preserved and rejected on read, not silently repaired.
        return self.read(key)
