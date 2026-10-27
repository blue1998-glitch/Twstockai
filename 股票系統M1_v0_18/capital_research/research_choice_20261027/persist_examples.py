"""Save three explicit intents using unchanged Journal; no generation or replay."""
from pathlib import Path
import json
from capital_research.research_choice_workflow import select_and_save, read_choice
from .fixtures import ROOT, load, materialize
from .build import save


def main():
    specs = [('grid-intent', 'grid-new-trigger', 'RECORDED_RESEARCH_INTENT'),
        ('conditional-intent', 'full-conditional', 'RECORDED_CONDITIONAL_RESEARCH_INTENT'),
        ('rejected-old-trigger', 'old-trigger-refused', 'REFUSED')]
    save(ROOT / 'journal-expected.json', [dict(key=key, source_case=case,
        storage_status='SAVED_AND_READ_BACK', read_status='READ_ONLY', choice_status=status)
        for key, case, status in specs])
    rows = []
    for key, case, status in specs:
        request = materialize(load(ROOT / 'cases' / case / 'input.json'))
        receipt = select_and_save(ROOT / 'journal', key, request)
        save(ROOT / 'receipts' / (key + '-select.json'), receipt)
        assert receipt['storage_status'] == 'SAVED_AND_READ_BACK'
        value = receipt['record']['value']
        assert value == load(ROOT / 'after-final' / case / 'actual.json')
        assert value['choice']['status'] == status
        read = read_choice(ROOT / 'journal', key)
        save(ROOT / 'receipts' / (key + '-read.json'), read)
        assert read['storage_status'] == 'READ_ONLY' and read['record'] == receipt['record']
        choice = value['choice']; selected = choice['selected']
        binding = choice['source_binding']
        view = dict(key=key, choice_status=status, reason=choice['requested_selection']['reason'],
            reasons=choice['reasons'], targets=selected['plan']['targets'] if selected else None,
            classification=selected['classification'] if selected else None,
            decision_at=binding['decision_at'], data_cutoff=binding['data_cutoff'],
            recorded_at=choice['recorded_at'], source_document_id=binding['source_document_id'],
            account_id=binding['account_id'], latest_decision_id=binding['latest_decision_id'],
            historical_token_count=len(binding['historical_reviewed_tokens']),
            decision_token_count=len(binding['decision_reviewed_tokens']),
            purpose=choice['purpose'], execution_authorized=choice['execution_authorized'],
            order_generation=choice['order_generation'], execution=choice['execution'])
        save(ROOT / 'views' / (key + '.json'), view)
        rows.append(dict(key=key, source_case=case, choice_status=status,
            exact_record_readback=True, original_actual_equal=True))
        print(key, status)
    save(ROOT / 'journal-actual.json', rows)


if __name__ == '__main__':
    main()
