"""Explicit supplemental SELECT or immutable READ; no generation route."""
import argparse
import json
from pathlib import Path
from .selection_supplement import select_supplement,read_supplement


def render_text(receipt):
    lines=['待選操作的明示補選（合成研究，不交易）','補選狀態：'+receipt['workflow_status'],
        '補選ID：'+str(receipt['supplement_id']),'保存狀態：'+json.dumps(receipt['storage'],ensure_ascii=False),
        '研究／核對狀態：'+json.dumps(receipt['observed'],ensure_ascii=False),'理由：'+json.dumps(receipt['reasons'],ensure_ascii=False)]
    b=receipt['parent_binding']
    if b is not None:
        lines+=['原操作：'+b['parent_operation_id'],'原等待結果：'+b['parent_result_id'],
            '原generation：'+b['generation_id'],'原資料截止：'+b['source_binding']['data_cutoff'],
            '原決策時間：'+b['source_binding']['decision_at']]
    v=receipt['supplement']
    if v is not None:
        lines+=['保存補選結果：'+v['outcome'],'明示選擇：'+json.dumps(v['requested_selection'],ensure_ascii=False),
            '補選紀錄時間：'+v['recorded_at']]
        lines.append('明示選中目標（未執行）：'+json.dumps(v['selected_targets'],ensure_ascii=False) if v['selected_targets'] is not None
            else '未選中，不改選其他候選。')
    return '\n'.join(lines+['原等待結果留史；沒有重新生成、重設資本或變更持股／權利／預留／token。',
        '等待交割仍是條件意圖；只記原截止研究，不代表今日交易資格。正式資格false，主壓力null。'])+'\n'


def main():
    p=argparse.ArgumentParser(description='沿已保存等待結果明示補選，不生成或交易')
    p.add_argument('operation',choices=('SELECT','READ'));p.add_argument('--parent-store',required=True)
    p.add_argument('--parent-id',required=True);p.add_argument('--store',required=True);p.add_argument('--id',required=True)
    p.add_argument('--input');p.add_argument('--format',choices=('text','json'),default='text');a=p.parse_args()
    if a.operation=='READ':
        if a.input:p.error('READ does not accept --input')
        receipt=read_supplement(a.parent_store,a.parent_id,a.store,a.id)
    else:
        if not a.input:p.error('SELECT requires explicit --input')
        try:request=json.loads(Path(a.input).read_text())
        except (OSError,ValueError) as exc:p.exit(2,'SUPPLEMENT_INPUT_FAILED: '+str(exc)+'\n')
        receipt=select_supplement(a.parent_store,a.parent_id,a.store,a.id,request)
    print(json.dumps(receipt,ensure_ascii=False,indent=2) if a.format=='json' else render_text(receipt),end='\n' if a.format=='json' else '')
    value=receipt['supplement']
    return 0 if value is not None and value['outcome'] in ('COMPLETED_SUPPLEMENT_INTENT','COMPLETED_SUPPLEMENT_CONDITIONAL_INTENT') else 2


if __name__=='__main__':raise SystemExit(main())
