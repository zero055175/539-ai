"""Aggregate prospective inference only; fixed first 300 scored draws."""
import json, math, hashlib
from datetime import datetime, timezone
from pathlib import Path
from research_cloud import write
from research34 import NAMES, PROTOCOL, digest, TZ
from cloud_backtest import P
ROOT=Path(__file__).resolve().parent/'docs/data'
TARGET=300
ALPHA=.05

def tail(k,n,p=P):
    if k<=0:return 1.
    if k>n:return 0.
    if p==0:return 0.
    if p==1:return 1.
    logs=[math.lgamma(n+1)-math.lgamma(j+1)-math.lgamma(n-j+1)+j*math.log(p)+(n-j)*math.log1p(-p) for j in range(k,n+1)]
    m=max(logs);return min(1.,math.exp(m)*sum(math.exp(x-m) for x in logs))

def holm(ps):
    out=[0.]*len(ps);prev=0.
    for i,j in enumerate(sorted(range(len(ps)),key=lambda j:ps[j])):
        prev=max(prev,min(1.,(len(ps)-i)*ps[j]));out[j]=prev
    return out

def wilson(k,n,z=1.95996398454):
    if not n:return None
    p=k/n;d=1+z*z/n;m=(p+z*z/(2*n))/d;r=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return [max(0,m-r),min(1,m+r)]

def report(root=ROOT):
    q=json.loads((root/'prospective34.json').read_text());h=json.loads((root/'history.json').read_text()); rows=h['rows']; actual={r['d']:r['n'] for r in rows}; records=q['records']; dates=[r['sealed']['date'] for r in records]; code=hashlib.sha256(Path(__file__).with_name('research34.py').read_bytes()).hexdigest()
    result=dict(version='35.0',baseline=P,target=TARGET,alpha=ALPHA,checked_at=datetime.now(timezone.utc).isoformat(),models=[],limitations='固定首300個已核對期；未達門檻不公布p值。Wilson區間為個別描述性區間；Holm控制七模型家族錯誤率。封存非第三方時間證明，未校正過往版本研究或選擇性缺期。')
    cutoff=next(k for k in range(TARGET+1) if tail(k,TARGET)<=ALPHA/len(NAMES))
    result['power']=[dict(assumed_rate=p,power=tail(cutoff,TARGET,p)) for p in [.12,.15,.18,.20]];result['conservative_threshold']=cutoff
    def valid(r):
        a=r['sealed'];d=a['date'];t=datetime.fromisoformat(a['created_at']).astimezone(TZ)
        return (r['state']!='blocked' and digest(a)==r['sha256'] and a['code']==code and t.date().isoformat()==d and t.hour<19 and digest([x for x in rows if x['d']<d])==a['history_sha256'] and set(a['samples'])==set(NAMES) and all(len(v)==5 and len(set(v))==5 and all(type(x)==int and 1<=x<=39 for x in v) for v in a['samples'].values()))
    if q['protocol']!=PROTOCOL or dates!=sorted(set(dates)) or not all(valid(r) for r in records):result.update(state='blocked',message='封存驗證失敗，停止檢定');return result
    scored=[]
    for r in records:
        a=r['sealed'];d=a['date']
        if d not in actual:
            if r['state']=='scored':result.update(state='blocked',message='已核對資料消失');return result
            break
        hits={m:len(set(v)&set(actual[d])) for m,v in a['samples'].items()}
        if r['state']!='scored' or r.get('actual')!=actual[d] or r.get('hits')!=hits:result.update(state='blocked',message='核對紀錄不一致');return result
        scored.append(hits)
    n=min(len(scored),TARGET); result.update(n=n,state='complete' if n==TARGET else 'collecting',message='固定樣本檢定完成' if n==TARGET else '累積盲測資料中；不進行中途顯著性檢定',first=dates[0] if n else None,last=dates[n-1] if n else None)
    for m in NAMES:
        k=sum(x[m]>=2 for x in scored[:n]); result['models'].append(dict(name=m,n=n,k=k,rate=k/n if n else None,ci=wilson(k,n),difference=k/n-P if n else None,p=tail(k,n) if n==TARGET else None,holm=None))
    if n==TARGET:
        for m,p in zip(result['models'],holm([m['p'] for m in result['models']])):m.update(holm=p,significant=p<=ALPHA)
    return result

if __name__=='__main__':
    r=report();write(ROOT/'inference35.json',r);print(r['message'])
