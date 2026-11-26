import unittest,tempfile,random
from datetime import datetime,timedelta
from pathlib import Path
from lite41 import TZ,write,read
from lite42 import build,backtest,diagnostics,summarize,PROBS
class Test42(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.now=datetime(2026,11,26,12,tzinfo=TZ);rng=random.Random(42)
  self.rows=[{'d':(self.now.date()-timedelta(days=i)).isoformat(),'n':sorted(rng.sample(range(1,40),5))} for i in range(1,45) if (self.now.date()-timedelta(days=i)).weekday()!=6][::-1]
  write(self.root/'history.json',{'rows':self.rows,'errors':['old archive unavailable'],'pending_months':['2007-01']})
 def tearDown(self):self.tmp.cleanup()
 def test_partial(self):
  q=build(self.root,self.now);self.assertEqual(q['n'],len(self.rows));self.assertEqual(q['backtest']['model']['n'],len(self.rows)-10);self.assertEqual(len(q['samples']),1);self.assertEqual(q['prospective']['n'],0)
  self.assertEqual(read(self.root/'history.json',{})['rows'],self.rows)
 def test_repeated(self):
  q=build(self.root,self.now);r=build(self.root,self.now);self.assertEqual(q['diagnostics'],r['diagnostics']);self.assertEqual(q['samples'],r['samples'])
 def test_score(self):
  q=build(self.root,self.now);write(self.root/'history.json',{'rows':self.rows+[{'d':'2026-11-26','n':q['samples'][0]['numbers']}]});r=build(self.root,self.now.replace(hour=22));self.assertEqual(r['prospective']['thresholds']['5']['hits'],1)
 def test_prefix(self):
  a=backtest(self.rows[:20]);b=backtest(self.rows[:21]);self.assertEqual(a['model']['n']+1,b['model']['n']);self.assertTrue(all(x<=y for x,y in zip(a['model']['distribution'],b['model']['distribution'])))
 def test_empty(self):
  write(self.root/'history.json',{'rows':[]});q=build(self.root,self.now);self.assertIsNone(q['diagnostics']);self.assertEqual(q['backtest']['model']['n'],0)
 def test_gap(self):
  write(self.root/'history.json',{'rows':self.rows[:-1]});q=build(self.root,self.now);self.assertFalse(q['samples']);self.assertGreater(q['backtest']['model']['n'],0)
 def test_math(self):
  self.assertAlmostEqual(sum(PROBS),1);self.assertAlmostEqual(PROBS[5],1/575757);self.assertAlmostEqual(summarize([0,0,0,0,0,1])['thresholds']['5']['rate'],1)
 def test_sync_error(self):
  q=build(self.root,self.now,sync_error='offline');self.assertEqual(q['quality']['sync_error'],'offline');self.assertGreater(q['n'],0)
if __name__=='__main__':unittest.main()
