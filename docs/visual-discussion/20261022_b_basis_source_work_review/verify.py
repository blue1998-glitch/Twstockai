"""Independent data/provenance and cutoff checks for this research only."""
import argparse, copy, hashlib, json
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from study import ROOT,START,CUTOFF,EVENT,SOURCE_SHA,blob,build,adjusted,load,dump

def verify(source):
    checks=[]
    def ok(name,test):
        assert test,name
        checks.append(name)
    before=source.read_bytes();source_data=load(source)
    evidence,views=build(source)
    ok('saved source exact original Git blob',blob(before)==SOURCE_SHA)
    ok('saved evidence and views reproduce',evidence==load(ROOT/'evidence.json') and views==load(ROOT/'comparison-data.json'))
    captures=load(ROOT/'source-capture.json')
    for r in captures:
        body=(ROOT/'raw'/(r['name']+'.json')).read_bytes()
        ok('retained response SHA '+r['name'],hashlib.sha256(body).hexdigest()==r['sha256'])
    ok('fresh June-July OHLCV 38 records / 190 fields match saved',evidence['fresh_raw_checks']=={'records':38,'ohlcv_fields':190,'all_equal':True})
    ok('same 133 market and stock dates; over six calendar months',[r['date'] for r in views['market']]==[r['date'] for r in views['raw']] and START=='2026-01-02' and CUTOFF=='2026-07-24' and len(views['raw'])==133)
    ratio=Fraction(3305,3445)
    exact_feb=Fraction(355,10)*ratio
    july=[b for b in views['raw'] if EVENT<=b['date']<=CUTOFF]
    ok('independent rational first post-action cross of February source',next(b['date'] for b in july if Fraction(b['close'])>exact_feb)=='2026-07-06')
    ok('independent rational post-July-source cross',next(b['date'] for b in july if b['date']>'2026-07-17' and Fraction(b['close'])>Fraction('35.50'))=='2026-07-20')
    ok('unadjusted share volume retained on every bar',all(a['volume_shares_scaled']==b['volume_shares_scaled'] for a,b in zip(views['raw'],views['single_event_candidate'])))
    ok('post-event all OHLC unchanged',all(all(Decimal(a[k])==Decimal(b[k]) for k in ['open','high','low','close']) for a,b in zip(views['raw'],views['single_event_candidate']) if a['date']>=EVENT))
    original=copy.deepcopy(source_data['bars'])
    for cutoff in ['2026-02-26','2026-06-30','2026-07-01','2026-07-06','2026-07-17','2026-07-20','2026-07-24']:
        clean=adjusted(original,cutoff)
        poison=copy.deepcopy(original)
        for b in poison:
            if b['date']>cutoff:
                for k in ['open','high','low','close']:b[k]='999999'
                b['volume_shares_scaled']='1'
        ok('future OHLCV exclusion '+cutoff,adjusted(poison,cutoff)==clean)
        ok('retained/truncated prefix '+cutoff,adjusted([b for b in original if b['date']<=cutoff],cutoff)==clean)
    pre,factor=adjusted(original,'2026-06-30')
    ok('July event not applied to pre-event analysis',factor=='1' and all(Decimal(a['close'])==Decimal(b['close']) for a,b in zip([b for b in original if START<=b['date']<EVENT],pre)))
    ok('future event cash mutation cannot change earlier analysis',adjusted(original,'2026-06-30',cash='2.7')==adjusted(original,'2026-06-30'))
    ok('pure transforms and saved source immutable',source_data['bars']==original and source.read_bytes()==before)
    ok('unknown strategy and policy remain unpromoted',evidence['market']['regime']=='NOT_ESTABLISHED' and evidence['market']['preferred_basis_under_policy'] is None and not evidence['scope']['historical_signal_eligible'] and not evidence['candidate_method']['complete_adjusted_history'])
    from PIL import Image
    for name in ['market-context','raw-reference','single-event-reference']:
        with Image.open(ROOT/(name+'.png')) as im:
            im.verify()
        ok('complete PNG '+name,True)
    from pypdf import PdfReader
    pdf=ROOT/'output/pdf/b-basis-source-review.pdf'
    reader=PdfReader(pdf)
    ok('three-page valid PDF',len(reader.pages)==3 and pdf.read_bytes().rstrip().endswith(b'%%EOF'))
    ok('vector charts without raster image objects',not any(obj.get_object().get('/Subtype')=='/Image' for page in reader.pages for obj in (page['/Resources'].get('/XObject') or {}).get_object().values()))
    report={'status':'PASS_RESEARCH_DATA_AND_RENDER_STRUCTURE_ONLY','checks':checks,'check_count':len(checks),'not_rerun':['original core','MACD','old research drivers','product/browser/Android suites'],'manual_visual_qa':'SEE manual-qa.json','historical_signal_eligible':False}
    dump(ROOT/'verification.json',report);print(report['status'],len(checks))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',required=True,type=Path);verify(p.parse_args().source)
