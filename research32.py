"""Fixed retrospective benchmark. Outputs aggregate evidence, not number recommendations."""
import json, math, hashlib
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
from cloud_backtest import research, upper, P
from research_cloud import write
ROOT=Path(__file__).resolve().parent/'docs/data'

def benchmark(rows):
    r=research(rows)
    cut=len(rows)-r['test']; N=r['test']
    extra={'短期10期頻率':[0]*6,'冷門100期頻率':[0]*6,'固定五元素對照':[0]*6}
    for i in range(cut,len(rows)):
        f=Counter(v for x in rows[i-100:i] for v in x['n']); s=Counter(v for x in rows[i-10:i] for v in x['n'])
        actual=set(rows[i]['n'])
        selections=[sorted(range(1,40),key=lambda v:(-s[v],v))[:5],sorted(range(1,40),key=lambda v:(f[v],v))[:5],range(1,6)]
        for (name,counts),a in zip(extra.items(),selections):
            k=len(actual.intersection(a)); counts[k]+=1
            year=r['yearly'][rows[i]['d'][:4]]; year['hits'][name]=year['hits'].get(name,0)+int(k>=2)
    for name,c in extra.items():
        k=sum(c[2:]); p=k/N; z=1.95996398454; den=1+z*z/N; mid=(p+z*z/(2*N))/den; rad=z*math.sqrt(p*(1-p)/N+z*z/(4*N*N))/den
        r['results'].append(dict(name=name,counts=c,rate=p,ci=[max(0,mid-rad),min(1,mid+rad)],p=upper(k,N)))
    for x in r['results']:
        x['adjusted']=min(1,x['p']*len(r['results'])); x['difference']=x['rate']-P; x['mean_hits']=sum(i*k for i,k in enumerate(x['counts']))/N
    r.update(version='32.0',protocol='fixed-100-warm-80-20-v1',kind='retrospective',limitations='固定九模型、同一歷史保留集；非前瞻盲測。重複執行或重疊測試不能視為獨立證據。資料完整性及來源真實性須另行核實。')
    return r

def run(root=ROOT):
    h=json.loads((root/'history.json').read_text(encoding='utf-8')); rows=h['rows']; dest=root/'benchmark32.json'; now=datetime.now(timezone.utc).isoformat()
    status=dict(version='32.0',checked_at=now,records=len(rows),pending_months=h.get('pending_months',[]),source_errors=h.get('errors',[]),secondary_status=h.get('secondary_status','未核對'))
    if len(rows)<300:
        status.update(state='insufficient',message='至少需要300期歷史資料');write(dest,status);return status
    key=hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    if dest.exists():
        old=json.loads(dest.read_text(encoding='utf-8'))
        if old.get('state')=='complete' and old.get('result',{}).get('sha256')==key and old['result'].get('protocol')=='fixed-100-warm-80-20-v1':
            status.update(state='complete',message='相同資料，沿用既有研究',result=old['result']);write(dest,status);return status
    try:
        r=benchmark(rows); status.update(state='complete',message='統一歷史回測完成',result=r);write(dest,status);return status
    except Exception as e:
        status.update(state='error',message=str(e));write(dest,status);raise
if __name__=='__main__':
    q=run();print(q['state'],q['message'])
