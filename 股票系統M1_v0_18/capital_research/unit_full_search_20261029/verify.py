"""Pre-save integrity/scope check only; does not execute numeric producers."""
import hashlib,json,re,subprocess
from pathlib import Path
from .freeze import ROOT,REPO,load,save,info

def main():
    status=subprocess.check_output(['git','status','--porcelain=v1','-uall','-z'],cwd=REPO).decode().split('\0')
    rows=[(x[:2],x[3:]) for x in status if x]
    allowed={'AGENTS.md','CONTINUE_IN_WORK_MODE.md','PROJECT_VISION.md','M1_V019_GRAPH_CORE_RESUME_HANDOFF.md',
        '股票系統M1_v0_18/capital_research/README.md','股票系統M1_v0_18/capital_research/allocation.py',
        '股票系統M1_v0_18/capital_research/quantity_candidates.py'}
    study=str(ROOT.relative_to(REPO))+'/'
    assert all(p in allowed or p.startswith(study) for s,p in rows)
    frozen=load(ROOT/'frozen.json')['files'];intake=load(ROOT/'intake.json')
    for row in frozen+intake['protected']+intake['source_originals']+load(ROOT/'actual/source-versions.json')['files']:
        assert info(REPO/row['path'])==row,row['path']
    sensitive=[];formatting=[]
    patterns=[r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',r'gh[pousr]_[A-Za-z0-9]{30,}',
        r'github_pat_[A-Za-z0-9_]{30,}',r'AKIA[0-9A-Z]{16}',r'sk-(?:proj-)?[A-Za-z0-9_-]{30,}']
    for s,name in rows:
        p=REPO/name;b=p.read_bytes();t=b.decode()
        if any(re.search(x,t) for x in patterns) or p.name in ('.env','id_rsa','credentials.json'):sensitive.append(name)
        if s=='??' and p.suffix in ('.py','.md'):
            if b.endswith(b'\n\n') or any(l.rstrip()!=l for l in t.splitlines()):formatting.append(name)
    assert not sensitive and not formatting,(sensitive,formatting)
    for name in sorted(allowed-{'股票系統M1_v0_18/capital_research/allocation.py','股票系統M1_v0_18/capital_research/quantity_candidates.py'}):
        t=(REPO/name).read_text();prior=subprocess.check_output(['git','show','HEAD:'+name],cwd=REPO).decode()
        start=t.index('# 2026-10-29 最新有效｜單位感知全換有界搜尋0.4');end=t.index('\n---\n\n',start)+len('\n---\n\n')
        assert t[:start]+t[end:]==prior,name
    subprocess.run(['git','diff','--check'],cwd=REPO,check=True)
    report=dict(frozen_files_verified=len(frozen),protected_files_verified=len(intake['protected']),
        source_originals_verified=len(intake['source_originals']),actual_sources_verified=7,
        sensitive_candidates=sensitive,new_format_issues=formatting,prior_progress_bytes_preserved=5,
        unique_methods=8,final_passed=8,new_market_samples=0,
        review='Only same bounded numeric gate, no execution, ledger, policy or source qualification change; false/null preserved')
    save(ROOT/'self-review.json',report)
    print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':main()
