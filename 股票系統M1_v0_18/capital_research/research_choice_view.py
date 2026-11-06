"""Pure text projection of one saved research intent. No engine or IO route."""
import json
from .research_choice import validate_record

LABELS = {
    'RECORDED_RESEARCH_INTENT': '一般研究意圖',
    'RECORDED_CONDITIONAL_RESEARCH_INTENT': '條件研究意圖（等待交割後重評）',
    'REFUSED': '遭拒（未選中）',
}


def _text(value):
    if value is None:
        return 'UNKNOWN（未保存）'
    return value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)


def render_text(saved):
    """Validate and display saved values only; input and source remain unchanged."""
    c = validate_record(saved)['choice']
    selection = c['requested_selection']
    selection = selection if isinstance(selection, dict) else {}
    selected = c['selected']
    target = '；'.join(code + '=' + shares for code, shares in sorted(selected['plan']['targets'].items())) if selected else '無（未選中）'
    lines = ['研究選擇紀錄（合成，只讀）',
        '意圖狀態：' + LABELS[c['status']],
        '選擇模式：' + _text(selection.get('mode')),
        '選擇理由：' + _text(selection.get('reason')),
        '目標股數（未執行）：' + target,
        '保存候選資格：' + (selected['classification'] if selected else '無（未選中）'),
        '拒絕理由：' + json.dumps(c['reasons'], ensure_ascii=False),
        '紀錄時間：' + _text(c['recorded_at']),
        '紀錄指紋：' + c['record_id']]
    b = c['source_binding']
    if b is None:
        lines.append('來源綁定：UNKNOWN（原拒絕紀錄未保存）')
    else:
        for label, key in [('資料截止', 'data_cutoff'), ('原決策時間', 'decision_at'),
            ('來源原件指紋', 'source_document_id'), ('generation指紋', 'generation_document_id'),
            ('帳戶指紋', 'account_id'), ('checkpoint指紋', 'checkpoint_id'),
            ('latest決策', 'latest_decision_id'), ('latest帳戶', 'latest_common_account_id')]:
            lines.append(label + '：' + _text(b.get(key)))
        lines.append('歷史reviewed token：' + str(len(b['historical_reviewed_tokens'])) +
            '；當期決策reviewed token：' + str(len(b['decision_reviewed_tokens'])))
    if selected:
        core = selected['core_evaluation']
        for label, key in [('保存條件', 'conditions'), ('下次重評條件', 'next_review_conditions'),
            ('取消條件', 'cancel_conditions')]:
            lines.append(label + '：' + _text(core.get(key)))
    return '\n'.join(lines + [
        '目標不是實際持股或成交；本紀錄未提供完整帳本，不重建現金、預留或成交量。',
        '文字只投影保存紀錄；來源指紋不是來源認證，紀錄時間不回填歷史可知時間。',
        '不重選、不建單、不成交；正式資格全部false，主壓力null。']) + '\n'
