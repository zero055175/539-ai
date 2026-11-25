"""Aggregate-only chronological generalization diagnostics. Not a selection engine."""
import json, random, math, hashlib
from datetime import date, datetime, timezone
from pathlib import Path
from research_cloud import write
from research35 import wilson
from cloud_backtest import P
ROOT=Path(__file__).resolve().parent/'docs/data'

def validate(rows):
    ds=[date.fromisoformat(x['d']) for x in rows]
    if ds!=sorted(set(ds)): raise ValueError('日期重複或順序錯誤')
    for x in rows:
        a=x['n']
        if len(a)!=5 or len(set(a))!=5 or any(type(v)!=int or not 1<=v<=39 for v in a): raise ValueError('獎號格式錯誤')

def features(prefix):
    # Diagnostic features only; no forecast or number output.
    return [sum(len(set(a['n']) & set(b['n'])) for a,b in zip(prefix[-30:-1],prefix[-29:]))/29, sum(sum(x['n']) for x in prefix[-30:])/30]

def observations(rows):
    # Study serial dependence through adjacent-draw overlap, not actionable selections.
    return [(rows[i]['d'],int(len(set(rows[i-1]['n'])&set(rows[i]['n']))>=2)) for i in range(1,len(rows))]

def summary(vals):
    n=len(vals);k=sum(vals);return dict(n=n,k=k,rate=k/n if n else None,ci=wilson(k,n))

def analyze(rows):
    validate(rows)
    n=len(rows);cut=int(n*.8); obs=observations(rows); train=[v for _,v in obs[:cut-1]];test=[v for _,v in obs[cut-1:]]
    # Prefix invariance: future rows cannot change any earlier diagnostic features.
    checks=[]
    for i in sorted({30,cut,n-1}):
        if 30<=i<n:
            changed=rows[:i]+[dict(x,n=[1,2,3,4,5]) for x in rows[i:]]
            checks.append(features(rows[:i])==features(changed[:i]) and observations(rows[:i])==observations(changed)[:i-1])
    rng=random.Random(3800); simulated=[]
    for _ in range(100):
        a=[dict(d=x['d'],n=rng.sample(range(1,40),5)) for x in rows]; simulated.append(summary([v for _,v in observations(a)[cut-1:]])['rate'])
    simulated.sort(); blocks=[dict(first=obs[i][0],last=obs[min(i+30,len(obs))-1][0],**summary([v for _,v in obs[i:i+30]])) for i in range(cut-1,len(obs)-29,30)]
    return dict(train=summary(train),test=summary(test),gap=sum(train)/len(train)-sum(test)/len(test),prefix_checks=len(checks),prefix_pass=all(checks),blocks=blocks,null_trials=100,null_interval=[simulated[2],simulated[97]],null_mean=sum(simulated)/100)

def run(root=ROOT):
    out=dict(version='38.0',checked_at=datetime.now(timezone.utc).isoformat(),baseline=P,limitations='相鄰開獎重疊為描述性診斷，不代表任何選號模型的預測力。前綴測試僅涵蓋本模組；模擬區間非正式顯著性檢定。歷史資料可能已被研究過。')
    try:
        h=json.loads((root/'history.json').read_text());rows=h['rows'];validate(rows)
        if h.get('errors') or h.get('pending_months'):out.update(state='blocked',message='資料同步有缺漏或錯誤')
        elif len(rows)<300:out.update(state='insufficient',message='至少需要300期資料')
        else:out.update(state='complete',message='歷史序列泛化診斷完成',result=analyze(rows),data_sha256=hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest())
    except (ValueError,KeyError,TypeError,OSError) as e:out.update(state='blocked',message=str(e))
    write(root/'generalization38.json',out);return out
if __name__=='__main__':print(run()['message'])
