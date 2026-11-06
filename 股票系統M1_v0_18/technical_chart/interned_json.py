"""Exact original chart JSON serialization; stdlib only, no engine imports."""
import json

def pack(value, *, base=None):
    """Lossless interned JSON tree transport; repeated subtrees share IDs, not numbers.
    This only changes HTML serialization, never the common data contracts.
    """
    nodes = list(base['nodes']) if base is not None else []
    seen = {json.dumps(n,ensure_ascii=False,separators=(',',':')):i for i,n in enumerate(nodes)}
    if base is not None and base.get('schema_version')!='chart-interned-json/0.1':raise ValueError('Unsupported interned anchor')
    def visit(v):
        if isinstance(v, bool) or v is None or isinstance(v, str):
            node = ['s',v]
        elif isinstance(v, (int,float)):
            if not isinstance(v,int) or abs(v)>9007199254740991:
                raise ValueError('Non-safe number; use original decimal/string contract')
            node = ['s',v]
        elif isinstance(v,list): node = ['a',*[visit(x) for x in v]]
        elif isinstance(v,dict): node = ['o',*[[k,visit(v[k])] for k in sorted(v)]]
        else: raise TypeError(type(v))
        token = json.dumps(node,ensure_ascii=False,separators=(',',':'))
        if token in seen: return seen[token]
        index=len(nodes);seen[token]=index;nodes.append(node);return index
    root=visit(value)
    return dict(schema_version='chart-interned-json/0.1',root=root,nodes=nodes)


def unpack(transport):
    memo={}
    def get(i):
        if i not in memo:
            n=transport['nodes'][i]
            memo[i] = n[1] if n[0]=='s' else [get(x) for x in n[1:]] if n[0]=='a' else {k:get(v) for k,v in n[1:]}
        return memo[i]
    return get(transport['root'])
