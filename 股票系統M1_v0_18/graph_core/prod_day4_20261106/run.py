"""One explicit saved-source day: exact gate -> original scan -> same owner.
Invoke under the existing unified-workspace lease. No scheduler or new endpoint.
"""
import json,resource
from . import intake,prepare
from graph_core.prod_core1_20261105 import flow as f,serve

def run():
    source=intake.run()
    if source['qualification']['status']!='SOURCE_QUALIFIED':return dict(status='BLOCKED_SOURCE',qualification=source['qualification'])
    sw=intake.WORK/'scan'
    with f.operation_budget(intake.WORK/'baseline-private.json'),f.lease(f.WORK):
        if not intake.store.c.exists(sw/'manifest-private.json'):prepare.prepare()
        result=f.saved(intake.TARGET,scanwork=sw)
        if result['status']!='COMPLETE':return result
        active=serve.activate(f.WORK)
        attempt=intake.WORK/'published-attempt-private.json'
        intake.store.put(intake.WORK,attempt,f.encode(dict(status='COMPLETE',target_date=intake.TARGET,as_of=intake.TARGET,reference=result['reference'],source_GETs=5,reused_tpex_GETs=0)))
        f.point(f.WORK,'latest-attempt-private.json',f.descriptor(attempt))
    return dict(status=result['status'],as_of=result['as_of'],reference=result['reference'],counts=result['counts'],source_GETs=source['this_execution_GETs'],new_core_calls=result['this_execution_new_core_calls'],new_records=result['this_execution_new_records'],reused=result['reused'],activation=active['status'])
if __name__=='__main__':
    resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2));print(json.dumps(run(),ensure_ascii=False))
