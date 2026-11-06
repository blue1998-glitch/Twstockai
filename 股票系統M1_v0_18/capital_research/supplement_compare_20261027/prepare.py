"""Freeze explicit READ fixtures and manifests; no source or account engine."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from capital_research.lifecycle import _fp

ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parents[1]
BASE=ROOT.parent/'selection_supplement_20261027/runs'
PARENT=ROOT.parent/'research_operation_20261027/initial/runs/no-selection'
PID='demo-no-selection'


def load(p):return json.loads(p.read_text())


def save(p,value):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')


def sign(value,key):value[key]=_fp({k:v for k,v in value.items() if k!=key})


def copy_records(src,target,identity,stages):
    result={}
    for stage in stages:
        name=identity+'--'+stage+'.json';result[stage]=load(src/name)
    return result


def write_records(target,identity,records):
    for stage,record in records.items():save(target/(identity+'--'+stage+'.json'),record)


def item(name,store,parent=PARENT,identity=None):
    return dict(label=name,parent_store=str(parent.relative_to(PROJECT)),parent_id=PID,
        store=str(store.relative_to(PROJECT)),id=identity or 'supp-'+store.name)


def main():
    parent=copy_records(PARENT,None,PID,['request','generation','result'])
    alt=deepcopy(parent);h=alt['request']['value'];request=json.loads(h['request_json'])
    request['recorded_at']='2026-10-27T13:00:00+08:00'
    h['request_json']=json.dumps(request,ensure_ascii=False,sort_keys=True,separators=(',',':'));h['request_id']=_fp(request);sign(h,'header_id')
    result=alt['result']['value'];result.update(header_id=h['header_id'],request_id=h['request_id']);sign(result,'result_id')
    alt_path=ROOT/'fixtures/alternate-parent';write_records(alt_path,PID,alt)
    conditional=copy_records(BASE/'conditional',None,'supp-conditional',['request','choice','result'])
    rebound=deepcopy(conditional);h=rebound['request']['value'];binding=h['request']['parent_binding']
    binding.update(parent_header_id=alt['request']['value']['header_id'],parent_request_id=alt['request']['value']['request_id'],parent_result_id=alt['result']['value']['result_id'])
    h['request_id']=_fp(h['request']);sign(h,'header_id')
    v=rebound['result']['value'];v.update(parent_binding=deepcopy(binding),request_id=h['request_id'],header_id=h['header_id']);sign(v,'result_id')
    rebound_path=ROOT/'fixtures/rebound-conditional';write_records(rebound_path,'supp-conditional',rebound)
    general=copy_records(BASE/'general',None,'supp-general',['request','choice','result'])
    partial=ROOT/'fixtures/incomplete-general';write_records(partial,'supp-general',{k:v for k,v in general.items() if k!='result'})
    changed=deepcopy(general);c=changed['choice']['value']['choice'];c['source_binding']['historical_reviewed_tokens']=[];sign(c,'record_id')
    token_path=ROOT/'fixtures/missing-token';write_records(token_path,'supp-general',changed)
    changed=deepcopy(general);h=changed['request']['value'];h['request']['parent_binding']['generation_id']='wrong-generation'
    h['request_id']=_fp(h['request']);sign(h,'header_id')
    generation_path=ROOT/'fixtures/wrong-generation';write_records(generation_path,'supp-general',changed)
    later=deepcopy(conditional);h=later['request']['value'];h['request']['recorded_at']='2026-10-27T13:00:00+08:00'
    h['request_id']=_fp(h['request']);sign(h,'header_id')
    c=later['choice']['value']['choice'];c['recorded_at']=h['request']['recorded_at']
    generation=parent['generation']['value']
    c['request_id']=_fp(dict(schema='capital-research-choice-input/0.1',synthetic=True,saved_result=generation,
        source_binding=c['source_binding'],selection=c['requested_selection'],recorded_at=c['recorded_at']))
    sign(c,'record_id')
    v=later['result']['value'];v.update(request_id=h['request_id'],header_id=h['header_id'],recorded_at=c['recorded_at'],choice_record_id=c['record_id'])
    v['source_check']['record_id']=c['record_id'];v['source_check']['choice_summary']['recorded_at']=c['recorded_at'];sign(v,'result_id')
    later_path=ROOT/'fixtures/later-conditional';write_records(later_path,'supp-conditional',later)
    g=item('一般',BASE/'general');c=item('條件',BASE/'conditional');rejected=item('拒絕對照',BASE/'unlisted-quantity')
    cases=[('general-vs-conditional',[g,c],'COMPARABLE',2,None),('with-refusal',[g,c,rejected],'COMPARABLE',3,None),
        ('same-parent-id-different-content',[g,item('另一原件',rebound_path,alt_path,'supp-conditional')],'REFUSED',0,'COMMON_CONDITIONS_MISMATCH'),
        ('incomplete-child',[g,item('部分保存',partial,identity='supp-general')],'REFUSED',0,'COMPLETE_SAVED_SUPPLEMENT_REQUIRED'),
        ('missing-token',[g,item('缺token',token_path,identity='supp-general')],'REFUSED',0,'COMPLETE_SAVED_SUPPLEMENT_REQUIRED'),
        ('wrong-generation',[g,item('錯generation',generation_path,identity='supp-general')],'REFUSED',0,'COMPLETE_SAVED_SUPPLEMENT_REQUIRED'),
        ('duplicate-label',[g,dict(c,label='一般')],'REFUSED',0,'UNIQUE_SINGLE_LINE_LABEL_REQUIRED'),
        ('resource-limit',[dict(g,label='欄'+str(n)) for n in range(9)],'REFUSED',0,'COMPARISON_RESOURCE_LIMIT_EXCEEDED'),
        ('later-record-time',[g,item('稍晚記錄',later_path,identity='supp-conditional')],'COMPARABLE',2,None)]
    specs=[]
    for name,items,status,columns,reason in cases:
        request=dict(schema='capital-supplement-comparison-read-input/0.1',synthetic=True,items=items)
        save(ROOT/'cases'/name/'input.json',request)
        save(ROOT/'cases'/name/'expected.json',dict(status=status,columns=columns,reason=reason))
        specs.append(dict(name=name,input_id=_fp(request),expected_status=status))
    save(ROOT/'case-index.json',specs)
    original_files=set(PARENT.glob('*.json'))
    for folder in [BASE/'general',BASE/'conditional',BASE/'unlisted-quantity']:original_files.update(folder.glob('*.json'))
    protected=[ROOT.parent/n for n in ['selection_supplement.py','selection_supplement_cli.py','research_operation.py','research_choice.py','research_choice_workflow.py','research_choice_source.py','lifecycle_compare.py','lifecycle.py','quantity_after_retry.py']]+[PROJECT/'rotation_research/store.py']
    def fingerprint(p):
        b=p.read_bytes();return dict(path=str(p.relative_to(PROJECT)),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
    save(ROOT/'intake.json',dict(base='841ab8cdd9750eb4915f69c5924d7bc8ffae52a6',initial_git=dict(tracked=0,index=0,untracked=0),
        originals=[fingerprint(p) for p in sorted(original_files)],protected_sources=[fingerprint(p) for p in protected],
        frozen=[fingerprint(p) for p in sorted(ROOT.rglob('*')) if p.is_file()]))
    print('Frozen nine comparison manifests/expectations, exact READ structural fixtures and original-source fingerprints.')


if __name__=='__main__':main()
