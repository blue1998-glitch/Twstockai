"""External immutable choice journal. No market data or calculation on read."""
import json, os
from pathlib import Path
from .core import validate_result

class ChoiceJournal:
    def __init__(self,path): self.root=Path(path)
    def _path(self,selection_id):
        import re
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,80}',selection_id): raise ValueError('Invalid selection ID')
        return self.root/(selection_id+'.json')
    def save(self,result):
        validate_result(result);self.root.mkdir(parents=True,exist_ok=True)
        path=self._path(result['intent']['selection_id'])
        body=(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
        try: fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        except FileExistsError:
            if path.is_symlink() or path.read_bytes()!=body: raise ValueError('Selection identity conflict; existing file preserved')
            return self.read(result['intent']['selection_id'])
        try:
            with os.fdopen(fd,'wb') as stream:
                stream.write(body);stream.flush();os.fsync(stream.fileno())
        except Exception:
            # A partial write remains visible for explicit diagnosis; never delete it.
            raise
        return self.read(result['intent']['selection_id'])
    def read(self,selection_id):
        path=self._path(selection_id)
        if path.is_symlink(): raise ValueError('Refuse symlink')
        value=json.loads(path.read_text());validate_result(value)
        if value['intent']['selection_id']!=selection_id: raise ValueError('Stored identity mismatch')
        return value
