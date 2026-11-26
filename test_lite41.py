import unittest,tempfile
from pathlib import Path
from datetime import datetime,date,timedelta
from lite41 import TZ,write,read,report,sync,clean,BASE
class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.now=datetime(2026,11,26,12,tzinfo=TZ)
  self.rows=[{'d':(self.now.date()-timedelta(days=i)).isoformat(),'n':[1,2,3,4,5]} for i in range(1,25) if (self.now.date()-timedelta(days=i)).weekday()!=6]
  write(self.root/'history.json',{'rows':self.rows,'pending_months':['2007-01'],'errors':['old source failed']})
 def tearDown(self): self.tmp.cleanup()
 def test_partial(self):
  q=report(self.root,self.now);self.assertEqual(q['n'],len(self.rows));self.assertEqual(len(q['samples']),1);self.assertEqual(q['windows']['100']['n'],len(self.rows));self.assertAlmostEqual(BASE,65621/575757)
  self.assertEqual(len(report(self.root,self.now)['samples']),1)
 def test_match(self):
  report(self.root,self.now);write(self.root/'history.json',{'rows':self.rows+[{'d':'2026-11-26','n':[1,2,3,6,7]}]});q=report(self.root,self.now.replace(hour=22));self.assertEqual(q['samples'][0]['hits'],3);self.assertEqual(q['scored'],1)
 def test_gap(self):
  write(self.root/'history.json',{'rows':self.rows[1:]});q=report(self.root,self.now);self.assertFalse(q['samples']);self.assertGreater(q['n'],0)
 def test_failure_preserves(self):
  def fail(m): raise OSError('offline')
  q=sync(self.root,self.now,fail);self.assertEqual(len(q['rows']),len(self.rows));self.assertTrue(q['errors']);self.assertEqual(len(report(self.root,self.now)['samples']),1)
 def test_invalid(self):
  by,bad,c=clean([{'d':'2026-11-25','n':[1,1,2,3,4]}],self.now.date());self.assertEqual(bad,1);self.assertFalse(by)
 def test_no_backdate(self): self.assertFalse(report(self.root,self.now.replace(hour=20))['samples'])
if __name__=='__main__':unittest.main()
