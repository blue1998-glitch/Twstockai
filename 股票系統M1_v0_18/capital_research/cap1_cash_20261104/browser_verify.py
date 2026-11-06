"""Actual Chromium QA; transient loopback, no owner/private data, no file://."""
from functools import partial
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
import threading,json,time,traceback,sys,shutil
from pathlib import Path
from playwright.sync_api import sync_playwright
from .build import CAP,ROOT,DELIVERY,MIN_FREE,write,sha
from .package import HTML_NAME


def run(label):
    outdir=CAP/('validation-'+label);outdir.mkdir(exist_ok=True)
    class Quiet(SimpleHTTPRequestHandler):
        def log_message(self,*a):pass
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(DELIVERY)))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    url='http://127.0.0.1:'+str(server.server_port)+'/'+HTML_NAME
    report=dict(schema='cap1-cash-browser/0.2',status='RUNNING',synthetic=True,android_device='NOT_TESTED_NEW_BUILD',
        file_scheme_tested=False,groups=[],daily_checks=[],downloads=[],screenshots=[],page_loads=[],errors=[])
    def screen(page,name):
        if shutil.disk_usage(ROOT).free<MIN_FREE+4*1024**2:raise ValueError('SCREENSHOT_CAPACITY_REFUSED')
        path=outdir/(name+'.png');page.screenshot(path=str(path),full_page=True)
        report['screenshots'].append(dict(path=str(path.relative_to(CAP)),sha256=sha(path.read_bytes())))
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
            for name,w,h,touch in [('portrait',390,844,True),('landscape',844,390,True),('desktop',1280,900,False)]:
                context=browser.new_context(viewport=dict(width=w,height=h),is_mobile=touch,has_touch=touch,device_scale_factor=1,accept_downloads=True)
                page=context.new_page();errors=[];requests=[]
                page.on('pageerror',lambda e:errors.append(str(e)));page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None);page.on('request',lambda r:requests.append(r.url))
                start=time.perf_counter();response=page.goto(url,wait_until='load');elapsed=time.perf_counter()-start
                assert response.status==200;data=page.locator('#cap1-data').evaluate('(el)=>JSON.parse(el.textContent)')
                assert set(data['branches'])=={'hold','reduce','partial','cash'}
                assert not page.locator('#technical').evaluate('(el)=>el.open') and not page.locator('#raw').is_visible()
                paths=None
                for key in ('hold','reduce','partial','cash'):
                    button=page.locator('[data-action="'+key+'"]');button.tap() if touch else button.click()
                    page.locator('#day').evaluate('(el)=>{el.value=7;el.dispatchEvent(new Event("input",{bubbles:true}));}')
                    assert button.get_attribute('aria-pressed')=='true'
                    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
                    b=data['branches'][key];m=b['metrics'];end=b['ledger']['daily'][-1]
                    def money(s):return s.rstrip('0').rstrip('.') if '.' in s else s
                    expected={'initial':money(m['initial_capital']),'terminal':money(m['terminal_accrual_equity']),
                        'cash':money(end['settled_cash']),'fees':money(m['costs']['recorded_fill_fee_tax']),
                        'receivable':money(end['cash_receivable']),'payable':money(end['purchase_payable']),
                        'return':format(float(m['statistics']['period_accrual_growth'])*100,'.3f')+'%',
                        'drawdown':format(float(m['statistics']['maximum_drawdown'])*100,'.3f')+'%'}
                    for ident,v in expected.items():assert page.locator('#'+ident).inner_text()==v,(key,ident,v)
                    assert page.locator('path[data-curve]').count()==4
                    current=page.locator('path[data-curve]').evaluate_all('(els)=>Object.fromEntries(els.map(e=>[e.dataset.curve,e.getAttribute("d")]))')
                    if paths is None:paths=current
                    else:assert current==paths
                    assert page.locator('#chart').evaluate('(e)=>Math.abs(e.viewBox.baseVal.width-e.clientWidth)<1')
                    assert ('已全現金' in page.locator('#cash-status').inner_text())==(key=='cash')
                    if key=='hold':assert page.locator('#recovery').inner_text()=='本期未發生回撤'
                    else:assert '尚未回復' in page.locator('#recovery').inner_text()
                    if name=='portrait' or key in ('hold','cash'):
                        page.evaluate('scrollTo(0,0)');screen(page,name+'-'+key)
                    if key=='cash':
                        if touch:page.locator('#day').tap(position=dict(x=page.locator('#day').bounding_box()['width']*.3,y=22))
                        for index,day,status,cash,claim in [(2,'2026-01-07','待交割','1000','235.76'),(4,'2026-01-09','已全現金','1235.76','0')]:
                            page.locator('#day').evaluate('(el,i)=>{el.value=i;el.dispatchEvent(new Event("input",{bubbles:true}));}',index)
                            assert page.locator('#date').inner_text()==day and status in page.locator('#cash-status').inner_text()
                            assert page.locator('#day-cash').inner_text()==cash and page.locator('#day-receivable').inner_text()==claim
                            assert page.locator('#day-payable').inner_text()=='0' and page.locator('#day-holdings').inner_text()=='無'
                            report['daily_checks'].append(dict(viewport=name,date=day,status=status,settled_cash=cash,unsettled=claim))
                            if name=='portrait':screen(page,name+'-cash-'+day)
                    report['groups'].append(dict(viewport=name,action=key,status='PASS'))
                page.locator('#technical summary').click();raw=json.loads(page.locator('#raw').inner_text())
                assert raw['branch']==data['branches']['cash']
                with page.expect_download() as event:page.locator('#download').click()
                body=Path(event.value.path()).read_bytes();assert json.loads(body)==data
                report['downloads'].append(dict(viewport=name,bytes=len(body),sha256=sha(body),complete_values_equal=True))
                assert not errors,errors;assert requests==[url],requests
                heap=context.new_cdp_session(page).send('Runtime.getHeapUsage')['usedSize']
                report['page_loads'].append(dict(viewport=name,html_bytes=len(response.body()),seconds=round(elapsed,3),js_heap_bytes=heap,js_errors=0,external_requests=0))
                context.close()
            browser.close()
        report['status']='PASS'
    except Exception:
        report['status']='FAIL';report['errors'].append(traceback.format_exc());raise
    finally:
        server.shutdown();server.server_close();write(outdir/'browser-verification.json',report)
        print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':run(sys.argv[1])
