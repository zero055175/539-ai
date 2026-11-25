"""Prospective research, fixed protocol; no proven predictive advantage."""
import json, hashlib, random, math
from collections import Counter
from datetime import datetime, timedelta, date, timezone
from pathlib import Path
from research_cloud import write
from cloud_backtest import upper, P
ROOT=Path(__file__).resolve().parent/'docs/data'
TZ=timezone(timedelta(hours=8))
PROTOCOL='v34-seven-fixed-models-v1'
NAMES=['隨機對照','長期頻率','近期加權','遺漏期數','貝氏全歷史','短期頻率','冷門頻率']
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def sample(rows,day):
    f=Counter(v for r in rows[-100:] for v in r['n']); s=Counter(v for r in rows[-10:] for v in r['n']); allf=Counter(v for r in rows for v in r['n']); gap={v:100 for v in range(1,40)}; w=Counter()
    for j,r in enumerate(reversed(rows[-100:])):
        for v in r['n']:gap[v]=min(gap[v],j);w[v]+=math.exp(-j/20)
    top=lambda score:sorted(sorted(range(1,40),key=lambda v:(-score(v),v))[:5])
    return dict(zip(NAMES,[sorted(random.Random(digest([day,PROTOCOL])).sample(range(1,40),5)),top(lambda v:f[v]),top(lambda v:w[v]),top(lambda v:gap[v]),top(lambda v:allf[v]),top(lambda v:s[v]),top(lambda v:-f[v])]))
def run(root=ROOT,now=None):
    now=(now or datetime.now(TZ)).astimezone(TZ); day=now.date().isoformat(); h=json.loads((root/'history.json').read_text()); rows=h['rows']; dates=[r['d'] for r in rows]; path=root/'prospective34.json'; q=json.loads(path.read_text()) if path.exists() else {'protocol':PROTOCOL,'records':[]}; code=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if dates!=sorted(set(dates)) or any(len(r['n'])!=5 or len(set(r['n']))!=5 or any(type(v)!=int or not 1<=v<=39 for v in r['n']) for r in rows):raise ValueError('invalid history')
    actual={r['d']:r['n'] for r in rows}; records=q['records']; msg='等待符合條件的新一期'; blocked=False
    if q['protocol']!=PROTOCOL:raise ValueError('protocol mismatch')
    for r in records:
        a=r['sealed']; d=a['date']; t=datetime.fromisoformat(a['created_at']).astimezone(TZ)
        if digest(a)!=r['sha256'] or a['code']!=code or t.date().isoformat()!=d or t.hour>=19 or digest([x for x in rows if x['d']<d])!=a['history_sha256']:
            r['state']='blocked';blocked=True;continue
        if d in actual:
            if 'actual' in r and r['actual']!=actual[d]:r['state']='blocked';blocked=True;continue
            r.update(state='scored',actual=actual[d],hits={name:len(set(nums)&set(actual[d])) for name,nums in a['samples'].items()})
    prev=now.date()-timedelta(days=1)
    while prev.weekday()==6:prev-=timedelta(days=1)
    if blocked:msg='封存或歷史資料變動，停止新增研究'
    elif any(r['sealed']['date']==day for r in records):msg='當日已封存，不重新產生'
    elif now.weekday()==6 or now.hour>=19 or day in actual:msg='非預設研究日或超過19:00截止'
    elif len(rows)<300 or dates[-1]!=prev.isoformat() or h.get('errors') or h.get('pending_months'):msg='歷史資料不足、缺漏或同步異常'
    else:
        a=dict(date=day,created_at=now.isoformat(),code=code,history_sha256=digest(rows),samples=sample(rows,day));records.append(dict(sealed=a,sha256=digest(a),state='pending'));msg='當期盲測樣本已封存'
    scored=[r for r in records if r['state']=='scored']; stats=[]
    for name in NAMES:
        counts=[sum(r['hits'][name]==k for r in scored) for k in range(6)]; n=len(scored); k=sum(counts[2:]); stats.append(dict(name=name,n=n,counts=counts,rate=k/n if n else None,adjusted_p=min(1,upper(k,300)*len(NAMES)) if n==300 else None))
    q.update(version='34.0',checked_at=now.isoformat(),message=msg,stats=stats,baseline=P,limitations='七模型固定協議；300期單次檢定，其他期數僅描述統計。Git與程式時間非第三方不可竄改證明；預設週一至六，特殊開獎日未核實。');write(path,q);return q
if __name__=='__main__':print(run()['message'])
