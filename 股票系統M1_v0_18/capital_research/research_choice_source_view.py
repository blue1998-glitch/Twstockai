"""Text projection of a saved-source consistency check; no IO or engines."""
import json


def _cell(value):
    return value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)


def render_text(result):
    lines = ['研究選擇與明示來源（合成，只讀）', '來源核對：' + result['check_status'],
        '原研究意圖狀態：' + _cell(result['choice_status'])]
    if result['check_status'] != 'MATCHED':
        return '\n'.join(lines + ['拒絕核對原因：' + _cell(result['reasons']),
            '不一致欄位：' + _cell(result['mismatch_fields']), '未提供相符並列；不重選或修復原件。']) + '\n'
    lines += ['候選快照角色：' + result['candidate_role'],
        '候選核對：' + result['candidate_check'],
        '保存候選資格：' + _cell(result['candidate_qualification']),
        '原意圖理由：' + _cell(result['choice_summary']['requested_selection']),
        '原拒絕理由：' + _cell(result['choice_summary']['reasons']),
        '紀錄時間：' + _cell(result['choice_summary']['recorded_at']),
        '欄位 | 選擇紀錄保存值 | 明示來源保存值']
    columns = result['columns']
    if result['candidate_check'] == 'NO_SAVED_CANDIDATE':
        lines.append('候選快照：無可核對快照；只證來源綁定相符，不推定已選中。')
    else:
        for label, get in [('候選ID', lambda c:c['candidate']['id']),
            ('目標股數（未執行）', lambda c:c['candidate']['plan']['targets']),
            ('保存候選資格', lambda c:c['candidate']['classification']),
            ('估計成本（非實際成交）', lambda c:c['candidate']['core_evaluation']['estimated_cost'])]:
            lines.append(label + ' | ' + ' | '.join(_cell(get(c)) for c in columns))
    for label, key in [('資料截止','data_cutoff'), ('原決策時間','decision_at'),
        ('來源指紋','source_document_id'), ('generation指紋','generation_document_id'),
        ('帳戶指紋','account_id'), ('checkpoint','checkpoint_id'),
        ('latest決策','latest_decision_id'), ('latest帳戶','latest_common_account_id')]:
        lines.append(label + ' | ' + ' | '.join(_cell(c['binding'][key]) for c in columns))
    for label, key in [('歷史reviewed token數','historical_reviewed_tokens'),
        ('當期決策reviewed token數','decision_reviewed_tokens')]:
        lines.append(label + ' | ' + ' | '.join(str(len(c['binding'][key])) for c in columns))
    return '\n'.join(lines + ['來源核對相符不代表候選合格；條件／拒絕意圖維持原狀。',
        '只核保存內容一致性，不認證來源；不重選、不改帳、不建單或成交。',
        '正式資格全部false，主壓力null；目標與估計成本不是實際持股或績效。']) + '\n'
