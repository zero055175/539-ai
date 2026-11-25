"""Pre-draw research sample, never a claim of improved odds."""
import json, hashlib, random
from pathlib import Path
from datetime import datetime, timedelta, timezone
from collections import Counter
from research_cloud import write
TZ=timezone(timedelta(hours=8))
ROOT=Path(__file__).resolve().parent/'docs/data'
def run(root=ROOT, now=None):
    now=now or datetime.now(TZ); now=now.astimezone(TZ); today=now.date(); day=today.isoformat()
    h=json.loads((root/'history.json').read_text()); rows=h['rows']; dates=[r['d'] for r in rows]
    if dates!=sorted(set(dates)) or any(len(r['n'])!=5 or len(set(r['n']))!=5 or any(type(v)!=int or not 1<=v<=39 for v in r['n']) for r in rows): raise ValueError('invalid history')
    path=root/'daily31.json'; q=json.loads(path.read_text()) if path.exists() else {'records':[]}; records=q['records']; actual={r['d']:r['n'] for r in rows}
    for r in records:
        if r['date'] in actual:
            r['hits']=len(set(r['numbers']) & set(actual[r['date']]));r['actual']=actual[r['date']]
    msg='尚未產生今日樣本'
    previous=today-timedelta(days=1)
    while previous.weekday()==6: previous-=timedelta(days=1)
    if any(r['date']==day for r in records): msg='今日樣本已封存，不重新選取'
    elif today.weekday()==6 or now.hour>=20 or day in actual: msg='非預設開獎日或已超過封存截止時間'
    elif len(rows)<300 or not dates or dates[-1]!=previous.isoformat(): msg='歷史資料不足或最新一期缺漏，不產生樣本'
    elif h.get('errors'): msg='同步有錯誤，暫不產生樣本'
    elif h.get('pending_months'): msg='歷史月份尚未補齊，暫不產生樣本'
    else:
        # Fixed Bayesian frequency experiment, not optimized on test data.
        recent=rows[-100:]; counts=Counter(v for r in recent for v in r['n']); fingerprint=hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        rng=random.Random(int(hashlib.sha256((day+fingerprint).encode()).hexdigest(),16)); tie={v:rng.random() for v in range(1,40)}
        numbers=sorted(sorted(range(1,40),key=lambda v:(-counts[v],tie[v]))[:5]); records.append(dict(date=day,created_at=now.isoformat(),numbers=numbers,history_sha256=fingerprint,model='固定100期貝氏頻率（同先驗）',hits=None));msg='今日研究樣本已封存'
    scored=[r for r in records if r.get('hits') is not None]; stats={}
    for n in (30,90,180):
        a=scored[-n:]; stats[str(n)]={'n':len(a),'at_least_2':sum(r['hits']>=2 for r in a),'distribution':[sum(r['hits']==k for r in a) for k in range(6)]}
    q.update(version='31.0',checked_at=now.isoformat(),message=msg,records=records,stats=stats,baseline=65621/575757);write(path,q);return q
if __name__=='__main__': print(run()['message'])
