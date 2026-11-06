"""Pure comparison of validated immutable READ receipts, never strategy scoring."""
from copy import deepcopy
import json
from .lifecycle import FLAGS, _fp, _signed
from .lifecycle_compare import MAX_ITEMS, DIAGNOSTIC_LIMIT, _differences

INPUT='capital-supplement-comparison-input/0.1'
SCHEMA='capital-supplement-comparison/0.1'


def _require(condition,reason):
    if not condition:raise ValueError(reason)


def validate_items(items,fields):
    _require(isinstance(items,list) and 2<=len(items)<=MAX_ITEMS,'COMPARISON_RESOURCE_LIMIT_EXCEEDED')
    labels=[]
    for item in items:
        _require(set(item)==fields,'EXPLICIT_COMPARISON_ITEM_REQUIRED')
        label=item['label']
        _require(isinstance(label,str) and bool(label.strip()) and not any(c in label for c in '\n\r|') and label not in labels,
            'UNIQUE_SINGLE_LINE_LABEL_REQUIRED')
        labels.append(label)


def empty_result():
    return dict(schema=SCHEMA,synthetic=True,status='REFUSED',comparable=False,refusals=[],
        differences=[],total_mismatches=0,details_truncated=False,common_binding=None,columns=[],provenance=[],
        scope='SAVED_MUTUALLY_EXCLUSIVE_RESEARCH_INTENTS_NOT_EXECUTIONS_OR_PERFORMANCE',
        ranking=None,selected_label=None,order_generation='NOT_PERFORMED',execution='NOT_PERFORMED',
        execution_authorized=False,primary_pressure_id=None,**{k:False for k in FLAGS})


def _research_only(value):
    _require(all(value[k] is False for k in FLAGS) and value['execution_authorized'] is False and
        value['primary_pressure_id'] is None and value['order_generation']==value['execution']=='NOT_PERFORMED',
        'RESEARCH_ONLY_SAVED_RESULTS_REQUIRED')


def _prepare(label,receipt):
    _require(receipt['schema']=='capital-selection-supplement-receipt/0.1' and receipt['mode']=='READ' and
        receipt['workflow_status']=='READ_ONLY' and receipt['storage']=={k:'READ_ONLY' for k in ('request','choice','result')} and
        receipt['generation']=='NOT_PERFORMED_REUSED_SAVED_PARENT' and receipt['supplement'] is not None,
        'COMPLETE_SAVED_SUPPLEMENT_REQUIRED')
    value=receipt['supplement'];_research_only(receipt);_research_only(value)
    _require(value['schema']=='capital-selection-supplement-result/0.1' and value['synthetic'] is True and
        receipt['supplement_id']==value['supplement_id'] and receipt['parent_binding']==value['parent_binding'],
        'SAVED_READ_RECEIPT_LINK_CONFLICT')
    _signed(value,'result_id');binding=value['parent_binding'];check=value['source_check'];candidate=None
    _require(receipt['observed']==dict(choice_status=value['choice_status'],check_status=check['check_status'] if check else None),
        'SAVED_READ_STATUS_CONFLICT')
    if value['outcome']=='SUPPLEMENT_CHOICE_REFUSED':
        _require(value['choice_status']=='REFUSED' and value['selected_targets'] is None and check is None,
            'REFUSED_CONTROL_CONFLICT')
    else:
        expected={'COMPLETED_SUPPLEMENT_INTENT':('RECORDED_RESEARCH_INTENT','CURRENTLY_FEASIBLE'),
            'COMPLETED_SUPPLEMENT_CONDITIONAL_INTENT':('RECORDED_CONDITIONAL_RESEARCH_INTENT','WAIT_SETTLEMENT_REASSESSMENT')}
        _require(value['outcome'] in expected,'SOURCE_CHECK_REFUSED_OR_UNSUPPORTED_OUTCOME')
        status,qualification=expected[value['outcome']]
        _require(value['choice_status']==status and check is not None and check['check_status']=='MATCHED' and
            check['candidate_check']=='EXACT_UNIQUE_MEMBER' and check['record_id']==value['choice_record_id'] and
            check['choice_status']==status and len(check['columns'])==2,'SAVED_SOURCE_CHECK_REQUIRED')
        _research_only(check)
        candidate=check['columns'][0]['candidate']
        _require(all(c['binding']==binding['source_binding'] and c['candidate']==candidate for c in check['columns']) and
            candidate['plan']['targets']==value['selected_targets'] and candidate['classification']==qualification,
            'SAVED_SOURCE_CHECK_CONTENT_CONFLICT')
    column=dict(label=label,supplement_id=value['supplement_id'],result_id=value['result_id'],outcome=value['outcome'],
        choice_status=value['choice_status'],source_check_status=check['check_status'] if check else None,
        candidate_qualification=candidate['classification'] if candidate else None,
        selected_targets=deepcopy(value['selected_targets']),requested_selection=deepcopy(value['requested_selection']),
        recorded_at=value['recorded_at'],estimated_cost=candidate['core_evaluation']['estimated_cost'] if candidate else None,
        reasons=deepcopy(value['reasons']))
    provenance=dict(label=label,result_id=value['result_id'],parent_result_id=binding['parent_result_id'],
        generation_id=binding['generation_id'],binding_id=_fp(binding))
    return binding,column,provenance


def compare_read_receipts(request):
    """Only saved READ projections. Files and original-source checks belong to the reader."""
    out=empty_result()
    try:
        _require(set(request)=={'schema','synthetic','items'} and request['schema']==INPUT and request['synthetic'] is True,
            'EXPLICIT_SYNTHETIC_COMPARISON_REQUIRED')
        validate_items(request['items'],{'label','receipt'})
        prepared=[]
        for item in request['items']:
            try:
                binding,column,provenance=_prepare(item['label'],item['receipt'])
                prepared.append((binding,column));out['provenance'].append(provenance)
            except (ValueError,KeyError,TypeError,IndexError,AttributeError) as exc:
                out['refusals'].append(dict(label=item['label'],reason=str(exc),
                    read_status=item['receipt'].get('workflow_status'),read_reasons=deepcopy(item['receipt'].get('reasons'))))
        if out['refusals']:return out
        reference=prepared[0]
        for binding,column in prepared[1:]:
            for diff in _differences(reference[0],binding,'/parent_binding'):
                out['total_mismatches']+=1
                if len(out['differences'])<DIAGNOSTIC_LIMIT:
                    out['differences'].append(dict(reference_label=reference[1]['label'],label=column['label'],**diff))
        out['details_truncated']=out['total_mismatches']>len(out['differences'])
        if out['total_mismatches']:
            out['refusals']=[dict(reason='COMMON_CONDITIONS_MISMATCH')];return out
        out.update(status='COMPARABLE',comparable=True,common_binding=deepcopy(reference[0]),
            columns=[deepcopy(c) for b,c in prepared])
    except (ValueError,KeyError,TypeError,IndexError,AttributeError) as exc:
        out['refusals'].append(dict(reason=str(exc)))
    return out


def _text(value):
    return value if isinstance(value,str) else json.dumps(value,ensure_ascii=False)


def render_text(result):
    lines=['同父補選意圖並列（合成，只讀，不排名）','共同條件狀態：'+result['status']]
    if result['status']!='COMPARABLE':
        return '\n'.join(lines+['拒比原因：'+_text(result['refusals']),'共同條件差異：'+_text(result['differences']),
            '未提供相符並列；不補資料、不重算或改選。'])+'\n'
    b=result['common_binding'];s=b['source_binding'];columns=result['columns']
    lines+=['共同父操作：'+b['parent_operation_id'],'共同父結果：'+b['parent_result_id'],
        '共同generation：'+b['generation_id'],'共同帳戶指紋：'+s['account_id'],
        '原資料截止：'+s['data_cutoff']+'；原決策時間：'+s['decision_at'],
        '欄位 | '+' | '.join(c['label'] for c in columns)]
    rows=[('保存意圖狀態',lambda c:c['choice_status']),
        ('目標（未執行）',lambda c:_text(c['selected_targets']) if c['selected_targets'] is not None else '未選中'),
        ('保存候選資格',lambda c:c['candidate_qualification'] or '無（拒絕對照）'),
        ('原件估計成本',lambda c:c['estimated_cost'] if c['estimated_cost'] is not None else '原件未提供'),
        ('來源核對',lambda c:c['source_check_status'] or '未執行'),
        ('明示請求',lambda c:_text(c['requested_selection'])),('補選紀錄時間',lambda c:c['recorded_at']),
        ('拒絕理由',lambda c:_text(c['reasons']))]
    for label,get in rows:lines.append(label+' | '+' | '.join(get(c) for c in columns))
    return '\n'.join(lines+['每欄是互斥研究意圖，不加總股數、成本或資金。',
        '條件意圖仍待交割重評，拒絕對照不變合格；較晚補記不變新決策。',
        '沒有後續行情或回放，不比較績效；不重選、評分、建單或成交。正式資格false，主壓力null。'])+'\n'
