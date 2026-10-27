from capital_research.research_choice import validate_record


def verify(request, expected, saved):
    validate_record(saved)
    r = saved['choice']
    assert r['status'] == expected['status'], (r['status'], r['reasons'])
    if expected['status'] == 'REFUSED':
        assert expected['reason'] in r['reasons'], r['reasons']
        assert r['selected'] is None
        return
    assert r['source_binding'] == request['source_binding']
    assert r['requested_selection'] == request['selection']
    assert r['recorded_at'] == request['recorded_at']
    assert r['selected']['classification'] == expected['classification']
    assert r['selected']['plan']['targets'] == expected['targets']
    assert r['selected']['feasible_for_research'] is True
