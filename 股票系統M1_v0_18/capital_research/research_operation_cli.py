"""Explicit RUN or immutable READ for a synthetic research operation."""
import argparse
import json
from pathlib import Path
from .research_operation import run_operation, read_operation, import_operation


def render_text(receipt):
    lines=['明示合成研究操作（不交易）','操作狀態：'+receipt['workflow_status'],
        '操作ID：'+str(receipt['operation_id']), '分階段保存：'+json.dumps(receipt['storage'],ensure_ascii=False),
        '已知階段結果：'+json.dumps(receipt['observed'],ensure_ascii=False),
        '理由：'+json.dumps(receipt['reasons'],ensure_ascii=False)]
    value=receipt['operation']
    if value is not None:
        lines+=['保存結果：'+value['outcome'],'來源核對：'+str(receipt['observed']['check_status']),
            '候選互斥；只有明示選擇，沒有最佳比例或自動勝者。']
        if value['source_check'] is not None and value['source_check']['check_status']=='MATCHED':
            checked=value['source_check']
            lines+=['明示選擇：'+json.dumps(checked['choice_summary']['requested_selection'],ensure_ascii=False),
                '明示選中目標（未執行）：'+json.dumps(checked['columns'][0]['candidate']['plan']['targets'],ensure_ascii=False)]
        elif value['outcome']=='AWAITING_EXPLICIT_SELECTION':
            lines.append('尚未明示選擇；停在候選清單，不自動續抱或續跑。')
        elif value['outcome']=='CHOICE_REFUSED':
            lines.append('已拒絕本次明示選擇；沒有選中或改選其他候選。')
        for c in value['candidate_catalog'] or []:
            lines.append(c['id']+' | '+c['classification']+' | '+json.dumps(c['plan']['targets'] if c['plan'] else None,ensure_ascii=False))
    lines+=['UNKNOWN不是保存成功；已存在ID只能明示READ，不自動重跑或修復。',
        '等待交割只記條件意圖；目標不是持股或成交。正式資格全部false，主壓力null。']
    return '\n'.join(lines)+'\n'


def main():
    p=argparse.ArgumentParser(description='明示合成研究RUN／IMPORT／READ，不建單或成交')
    p.add_argument('operation',choices=('RUN','IMPORT','READ'));p.add_argument('--store',required=True)
    p.add_argument('--id',required=True);p.add_argument('--input');p.add_argument('--format',choices=('text','json'),default='text')
    a=p.parse_args()
    if a.operation=='READ':
        if a.input:p.error('READ does not accept --input')
        receipt=read_operation(a.store,a.id)
    else:
        if not a.input:p.error(a.operation+' requires explicit --input')
        try:request=json.loads(Path(a.input).read_text())
        except (OSError,ValueError) as exc:p.exit(2,'OPERATION_INPUT_FAILED: '+str(exc)+'\n')
        receipt=(import_operation if a.operation=='IMPORT' else run_operation)(a.store,a.id,request)
    print(json.dumps(receipt,ensure_ascii=False,indent=2) if a.format=='json' else render_text(receipt),end='\n' if a.format=='json' else '')
    outcome=receipt['operation']['outcome'] if receipt['operation'] else None
    return 0 if receipt['workflow_status'] in ('COMPLETED_RESEARCH_INTENT','COMPLETED_CONDITIONAL_INTENT','READ_ONLY') and outcome in ('COMPLETED_RESEARCH_INTENT','COMPLETED_CONDITIONAL_INTENT') else 2


if __name__=='__main__':raise SystemExit(main())
