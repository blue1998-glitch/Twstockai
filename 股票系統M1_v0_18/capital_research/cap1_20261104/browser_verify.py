"""Transient loopback QA of a pure synthetic HTML, never file:// or owner data."""
import functools, http.server, threading, json, time, hashlib, sys, traceback, shutil
from pathlib import Path
from playwright.sync_api import sync_playwright
from .build import CAP, DELIVERY, ROOT, MIN_FREE, write
from .package import HTML_NAME


def run(label):
    outdir=CAP/('validation-'+label);outdir.mkdir(exist_ok=True)
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self,*args):pass
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(DELIVERY)))
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    url='http://127.0.0.1:'+str(server.server_port)+'/'+HTML_NAME
    report=dict(schema='cap1-browser-verification/0.1',synthetic=True,engine_calls=0,
        android_actual_device='NOT_TESTED_NEW_BUILD',file_scheme_tested=False,
        status='RUNNING',action_groups=[],downloads=[],touch_date_queries=[],screenshots=[],errors=[])
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
            for name,w,h,touch in [('portrait',390,844,True),('landscape',844,390,True),('desktop',1280,900,False)]:
                context=browser.new_context(viewport=dict(width=w,height=h),is_mobile=touch,has_touch=touch,device_scale_factor=1,accept_downloads=True)
                page=context.new_page();errors=[];requests=[];page.on('pageerror',lambda e:errors.append(str(e)))
                page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
                page.on('request',lambda r:requests.append(r.url))
                start=time.perf_counter();response=page.goto(url,wait_until='load');elapsed=time.perf_counter()-start
                assert response.status==200
                payload=page.locator('#cap1-data').evaluate('(el)=>JSON.parse(el.textContent)')
                assert not page.locator('#technical').evaluate('(e)=>e.open')
                assert not page.locator('#raw').is_visible()
                for key in ('hold','reduce','exit_b','cash'):
                    b=page.locator('[data-action="'+key+'"]');b.tap() if touch else b.click()
                    assert b.get_attribute('aria-pressed')=='true'
                    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                    if key=='cash':
                        assert page.locator('#blocked').is_visible() and not page.locator('#results').is_visible()
                        assert payload['unavailable']['metrics'] is None
                    else:
                        m=payload['branches'][key]['metrics'];ledger=payload['branches'][key]['ledger']
                        def money(v):return v.rstrip('0').rstrip('.') if '.' in v else v
                        expected={'initial':money(m['initial_capital']),'terminal':money(m['terminal_accrual_equity']),
                            'fees':money(m['costs']['recorded_fill_fee_tax']),'cash':money(ledger['daily'][-1]['settled_cash']),
                            'return':format(float(m['statistics']['period_accrual_growth'])*100,'.3f')+'%',
                            'drawdown':format(float(m['statistics']['maximum_drawdown'])*100,'.3f')+'%'}
                        for ident,v in expected.items():assert page.locator('#'+ident).inner_text()==v,(ident,v)
                        assert page.locator('path[data-curve]').count()==3
                        assert page.locator('#chart').evaluate('(el)=>Math.abs(el.viewBox.baseVal.width-el.clientWidth)<1')
                        assert page.locator('#chart text').evaluate_all('(els)=>els.every(e=>Number(e.getAttribute("font-size"))>=11)')
                        # All actions use identical fixed geometry and eight saved rows.
                        paths=page.locator('path[data-curve]').evaluate_all('(els)=>Object.fromEntries(els.map(e=>[e.dataset.curve,e.getAttribute("d")]))')
                        if key=='hold':original_paths=paths
                        else:assert paths==original_paths
                        assert '尚未回復' in page.locator('#recovery').inner_text()
                        if touch:
                            page.locator('#day').tap(position=dict(x=page.locator('#day').bounding_box()['width']*.58,y=22))
                        page.locator('#day').evaluate('(el)=>{el.value=4;el.dispatchEvent(new Event("input",{bubbles:true}));}')
                        assert page.locator('#date').inner_text()=='2026-01-09'
                        assert page.locator('#day-cash').inner_text()=='858.86'
                        assert page.locator('#day-holdings').inner_text().endswith('C 2股')
                        report['touch_date_queries'].append(dict(viewport=name,action=key,method='touch then exact range event' if touch else 'range event',settled_cash='858.860'))
                        page.locator('#day').evaluate('(el)=>{el.value=7;el.dispatchEvent(new Event("input",{bubbles:true}));}')
                    if name=='portrait' or key in ('hold','reduce'):
                        page.evaluate('scrollTo(0,0)');path=outdir/(name+'-'+key+'.png');
                        if shutil.disk_usage(ROOT).free < MIN_FREE+4*1024**2:raise ValueError('SCREENSHOT_CAPACITY_REFUSED')
                        page.screenshot(path=str(path),full_page=True)
                        report['screenshots'].append(dict(path=str(path.relative_to(CAP)),sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
                    report['action_groups'].append(dict(viewport=name,action=key,status='PASS'))
                page.locator('[data-action="reduce"]').click();page.locator('#technical summary').click()
                raw=json.loads(page.locator('#raw').inner_text());assert raw['branch']==payload['branches']['reduce']
                assert raw['source_manifest']==payload['source_manifest']
                with page.expect_download() as dl:page.locator('#download').click()
                download=dl.value;body=Path(download.path()).read_bytes();assert json.loads(body)==payload
                report['downloads'].append(dict(viewport=name,bytes=len(body),sha256=hashlib.sha256(body).hexdigest(),exact_payload=True))
                assert not errors,errors
                assert requests==[url],requests
                cdp=context.new_cdp_session(page);heap=cdp.send('Runtime.getHeapUsage')['usedSize']
                report.setdefault('page_loads',[]).append(dict(viewport=name,html_bytes=len(response.body()),load_seconds=round(elapsed,3),js_heap_after_interaction_bytes=heap,external_requests=0,js_errors=0))
                context.close()
            browser.close()
        report['status']='PASS'
    except Exception:
        report['status']='FAIL';report['errors'].append(traceback.format_exc());raise
    finally:
        server.shutdown();server.server_close()
        write(outdir/'browser-verification.json',report)
        print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':run(sys.argv[1])
