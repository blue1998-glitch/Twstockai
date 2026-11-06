"""Focused financial accounting and temporal-integrity tests; synthetic fixtures explicit."""
import copy, json, tempfile, unittest
from decimal import Decimal as D
from pathlib import Path
from .core import replay, compare, evidence, fees
from .store import Journal

def fixture():
    from datetime import date,timedelta
    bars=[]
    for i in range(75):
        p=D(100+i)
        bars.append({'date':str(date(2025,1,1)+timedelta(days=i)),
                     'open':str(p),'high':str(p+1),'low':str(p-1),'close':str(p),
                     'volume':str(10000000+i*10000)})
    return {'schema':'rotation-input/0.1','mode':'RAW','strict':False,'proxy_window':20,
            'initial_shares':1000,'initial_cash':'0','corporate_actions':[],
            'execution':{'fee_rate':'0.001425','minimum_fee':'20','sell_tax':'0.003',
                         'slippage_bps':'10','participation':'0.01','lot':100,'settlement_lag':0},
            'eligibility':{'company_actions':'UNVERIFIED','calendar':'UNVERIFIED','historical_availability':'UNVERIFIED'},
            'assets':{c:{'source_id':'SYNTHETIC-'+c,'basis_id':'SYNTHETIC-RAW-'+c,
                         'volume_unit':'SHARES_REPORTED','bars':copy.deepcopy(bars)} for c in ('A','B')}}

class CoreTests(unittest.TestCase):
    def setUp(self): self.data=fixture();self.cutoff=self.data['assets']['A']['bars'][25]['date']
    def run_plan(self,p='full',h=20,data=None): return replay(data or self.data,'A','B',self.cutoff,h,p)
    def test_same_start_and_costs(self):
        rs=compare(self.data,'A','B',self.cutoff,20)
        self.assertEqual({r['metrics']['initial_equity'] for r in rs.values()},{'125000'})
        self.assertEqual(rs['hold']['metrics']['orders'],0)
        self.assertGreater(D(rs['hold']['metrics']['estimated_terminal_exit_cost']),0)
        self.assertEqual(rs['cash']['metrics']['orders'],1)
        self.assertLess(D(rs['full']['metrics']['net_value_vs_hold']),0)
    def test_cash_flow_conservation_every_day(self):
        for p in ('hold','full','staged25','staged50','cash','delay5'):
            r=self.run_plan(p);cash=D(0);q={'A':1000,'B':0}
            for point,allocation in zip(r['nav'],r['allocation']):
                for t in [x for x in r['trades'] if x['date']==point['date']]:
                    cash+=D(t['cash_flow']);q[t['code']]+=t['shares']*(1 if t['side']=='BUY' else -1)
                self.assertEqual(q,allocation['shares']);self.assertEqual(cash,D(allocation['cash']))
                equity=cash+sum(q[c]*D(next(b['close'] for b in self.data['assets'][c]['bars'] if b['date']==point['date'])) for c in q)
                self.assertEqual(equity,D(point['mark_equity']));self.assertGreaterEqual(cash,0)
    def test_future_poison_does_not_change_decision(self):
        original=evidence(self.data['assets']['B'],self.cutoff)
        changed=copy.deepcopy(self.data)
        for b in changed['assets']['B']['bars'][26:]:
            for k in ('open','high','low','close'): b[k]=str(D(b[k])*100)
            b['volume']='999999999999'
        self.assertEqual(original,evidence(changed['assets']['B'],self.cutoff))
    def test_prefix_replay_identity(self):
        full=self.run_plan('staged25',40);short=self.run_plan('staged25',5)
        for key in ('nav','decisions','allocation'):
            self.assertEqual(full[key][:5],short[key])
        self.assertEqual([t for t in full['trades'] if t['date']<=short['nav'][-1]['date']],short['trades'])
    def test_next_open_never_same_close(self):
        r=self.run_plan()
        self.assertTrue(all(t['decision_cutoff'] < t['date'] for t in r['trades']))
        self.assertEqual(r['trades'][0]['raw_open'],'126')
    def test_fee_and_tax_rounding(self):
        self.assertEqual(fees(D(10000),self.data['execution'],True),(D(20),D(30)))
        self.assertEqual(fees(D(0),self.data['execution'],True),(D(0),D(0)))
    def test_settlement_cash_receivable_not_spendable(self):
        d=copy.deepcopy(self.data);d['execution']['settlement_lag']=2
        r=self.run_plan(data=d)
        self.assertEqual(r['allocation'][0]['cash'],'0')
        self.assertGreater(D(r['allocation'][0]['receivable']),0)
        buy=next(t for t in r['trades'] if t['side']=='BUY')
        self.assertEqual(buy['date'],d['assets']['B']['bars'][28]['date'])
    def test_volume_limit_uses_previous_not_current_day(self):
        d=copy.deepcopy(self.data);d['execution']['participation']='0.000001'
        r=self.run_plan(data=d);self.assertEqual(r['trades'],[]);self.assertTrue(r['blocks'])
        d['assets']['A']['bars'][26]['volume']='999999999999'
        changed=self.run_plan(data=d)
        self.assertEqual([t for t in changed['trades'] if t['date']==changed['nav'][0]['date']],[])
    def test_missing_calendar_refused(self):
        d=copy.deepcopy(self.data);d['assets']['B']['bars'].pop(30)
        with self.assertRaisesRegex(ValueError,'calendars'):self.run_plan(data=d)
    def test_missing_quote_refused_without_fill(self):
        d=copy.deepcopy(self.data);bar=d['assets']['B']['bars'][30]
        bar.update({k:None for k in ('open','high','low','close')});bar['missing']=True
        with self.assertRaisesRegex(ValueError,'Missing quote'):self.run_plan(data=d)
    def test_strict_eligibility_refused(self):
        d=copy.deepcopy(self.data);d['strict']=True
        with self.assertRaisesRegex(ValueError,'Company actions'):self.run_plan(data=d)
    def test_unknown_basis_and_actions_refused(self):
        for key,value in [('mode','Adjusted'),('corporate_actions',[{'cash':'1'}])]:
            d=copy.deepcopy(self.data);d[key]=value
            with self.assertRaises(ValueError):self.run_plan(data=d)
    def test_horizon_never_truncated(self):
        with self.assertRaisesRegex(ValueError,'Insufficient'):self.run_plan(h=60)
    def test_false_breakout_loss_and_staging_risk(self):
        d=copy.deepcopy(self.data)
        for b in d['assets']['A']['bars']:
            b.update(open='125',high='126',low='124',close='125')
        for b in d['assets']['B']['bars'][26:]:
            b.update(open='126',high='127',low='79',close='80',volume='1000000')
        rs=compare(d,'A','B',self.cutoff,20)
        self.assertLess(D(rs['full']['metrics']['net_value_vs_hold']),0)
        self.assertGreater(D(rs['staged25']['metrics']['end_net_liquidation_equity']),D(rs['full']['metrics']['end_net_liquidation_equity']))
        self.assertFalse(rs['staged25']['input_evidence']['B']['action_eligible'])
    def test_raw_source_unchanged(self):
        before=copy.deepcopy(self.data);self.run_plan();self.assertEqual(self.data,before)
    def test_repeated_loop_single_account_conservation(self):
        from .loop import replay_loop
        for policy in ('hold','full_review10','half_review10','cash_review10'):
            r=replay_loop(self.data,self.cutoff,self.data['assets']['A']['bars'][65]['date'],policy)
            cash=D(0);q={'A':1000,'B':0}
            for p in r['curve']:
                for t in [t for t in r['ledger'] if t['date']==p['date']]:
                    cash+=D(t['cash_flow']);q[t['code']]+=t['shares']*(1 if t['side']=='BUY' else -1)
                    self.assertLess(t['decision_cutoff'],t['date'])
                self.assertEqual(cash,D(p['cash']));self.assertEqual(q,p['shares'])
                self.assertGreaterEqual(cash,0);self.assertGreaterEqual(min(q.values()),0)
            self.assertEqual(r['external_flow'],'0')
    def test_loop_prefix_no_future_rewrite(self):
        from .loop import replay_loop
        ds=[b['date'] for b in self.data['assets']['A']['bars']]
        a=replay_loop(self.data,self.cutoff,ds[45],'half_review10')
        b=replay_loop(self.data,self.cutoff,ds[65],'half_review10')
        self.assertEqual(a['curve'],b['curve'][:20]);self.assertEqual(a['decisions'],b['decisions'][:2])
    def test_immutable_store_and_read_has_no_engine(self):
        with tempfile.TemporaryDirectory() as td:
            j=Journal(td);r=self.run_plan();self.assertEqual(j.save('example',r),j.read('example'))
            self.assertEqual(j.save('example',r),j.read('example'))
            with self.assertRaises(ValueError):j.save('example',{'changed':True})
            self.assertEqual(j.read('example')['value'],r)
            self.assertNotIn('core',Path(__file__).with_name('store.py').read_text())
            with self.assertRaises(ValueError):j.read('../escape')

if __name__=='__main__':unittest.main()
