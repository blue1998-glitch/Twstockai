"""Save the no-revocation control for the existing future-prefix assertion."""
import hashlib
import json
from pathlib import Path
from ..fixtures import specification, materialize
from ..reproduce import save


if __name__=='__main__':
    out=Path(__file__).parent
    spec=specification('future-revocation')
    spec['second_fact']['validity']['invalidation']=None
    save(out/'specification.json',spec)
    save(out/'first-input.json',spec['first_input'])
    save(out/'expected.json',dict(numeric_decision_equal=True,raw_fact_sources_equal=False,synthetic=True))
    save(out/'source-versions.json',dict(
        engine_sources=json.loads((out.parent/'after-final/source-versions.json').read_text()),
        generator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()))
    result=materialize(spec,record=lambda tag,value:save(out/(tag+'.json'),value))
    save(out/'actual.json',dict(resumed=result['resumed'],execution=result['execution'],
        checkpoint_states=[c['state'] for c in result['checkpoints']]))
    reference=json.loads((out.parent/'after-final/future-revocation/actual.json').read_text())
    comparison=dict(numeric_decision_equal=result['resumed']['decision']==reference['resumed']['decision'],
        raw_fact_sources_equal=result['execution']['fact_sources']==reference['execution']['fact_sources'],
        numeric_decision_id=result['resumed']['decision']['decision_id'],
        full_source_integrity_is_outside_numeric_equality=True,synthetic=True,independent_market_samples=0)
    save(out/'comparison.json',comparison)
    print(json.dumps(comparison))
    if not comparison['numeric_decision_equal'] or comparison['raw_fact_sources_equal']:
        raise SystemExit('Unexpected future-prefix comparison; retain diagnostics')
