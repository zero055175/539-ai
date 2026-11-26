"""V42: descriptive quality and reproducible evaluation of the unchanged V41 method."""
import math, random, hashlib, json
from itertools import combinations
from collections import Counter, deque
from datetime import datetime
from lite41 import TZ, ROOT, BASE, read, write, clean, sync, report

VERSION='42.0'
TOTAL=math.comb(39,5)
PROBS=[math.comb(5,k)*math.comb(34,5-k)/TOTAL for k in range(6)]

def wilson(k,n):
    if not n:return None
    z=1.959963984540054; p=k/n; d=1+z*z/n; c=(p+z*z/(2*n))/d; h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return [max(0,c-h),min(1,c+h)]

def summarize(hist):
    n=sum(hist)
    return {'n':n,'distribution':hist,'thresholds':{str(k):{'hits':sum(hist[k:]),'rate':sum(hist[k:])/n if n else None,'baseline':sum(PROBS[k:]),'ci95':wilson(sum(hist[k:]),n)} for k in range(2,6)}}

def backtest(rows):
    # Fixed predeclared rule; no parameter selection. Each test uses only earlier records.
    window=deque(); count=Counter(); hist=[0]*6; control=[0]*6; rng=random.Random(42001)
    dates=[]
    for row in rows:
        if len(window)>=10:
            chosen=sorted(range(1,40),key=lambda n:(-count[n],n))[:5]
            actual=set(row['n']); hist[len(actual.intersection(chosen))]+=1
            control[len(actual.intersection(rng.sample(range(1,40),5)))]+=1; dates.append(row['d'])
        window.append(row['n']); count.update(row['n'])
        if len(window)>100: count.subtract(window.popleft())
    return {'method':'固定最近最多100筆頻率；至少10筆暖身；僅使用當期前資料','start':dates[0] if dates else None,'end':dates[-1] if dates else None,'model':summarize(hist),'random_control':summarize(control),'seed':42001,'note':'探索性歷史回測；缺期未補值；不是未來獨立驗證，也不是中獎機率預估。'}

def diagnostics(rows):
    n=len(rows)
    if not n:return None
    single=Counter(); pair=Counter(); triple=Counter()
    for r in rows:
        a=r['n']; single.update(a);pair.update(combinations(a,2));triple.update(combinations(a,3))
    def stats(c,k):
        universe=math.comb(39,k); expected=n*math.comb(5,k)/universe
        return {'observed_distinct':len(c),'possible':universe,'expected_per_group':expected,'max_count':max(c.values(),default=0),'zero_groups':universe-len(c)}
    expected=n*5/39
    def statistic(c):return sum((c[i]-expected)**2/expected for i in range(1,40))
    observed=statistic(single); rng=random.Random(42002); B=199; exceed=0
    for _ in range(B):
        c=Counter()
        for j in range(n):c.update(rng.sample(range(1,40),5))
        exceed+=statistic(c)>=observed-1e-12
    # One prespecified global test; correct within-draw sampling without replacement.
    return {'n':n,'pair':stats(pair,2),'triple':stats(triple,3),'frequency_global':{'statistic':observed,'p_monte_carlo':(exceed+1)/(B+1),'replicates':B,'seed':42002},'bayes_marginal':{str(i):(single[i]+20*5/39)/(n+20) for i in range(1,40)},'note':'全域頻率檢定僅檢查邊際分布；共現為描述性統計；貝氏平滑使用20期等效先驗，均不作為未來預測機率。缺期或選擇性資料會影響解讀。'}

def build(root=ROOT,now=None,sync_error=None):
    now=(now or datetime.now(TZ)).astimezone(TZ)
    q=report(root,now) # preserve existing V41 protocol and ledger; do not switch models
    h=read(root/'history.json',{'rows':[]}); by,bad,conflicts=clean(h['rows'],now.date()); rows=[{'d':d,'n':v} for d,v in sorted(by.items())]
    key=hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest(); p=root/'lite42.json'; old=read(p,{})
    if old.get('data_sha256')==key and old.get('version')==VERSION and 'diagnostics' in old and 'backtest' in old:
        d=old['diagnostics']; b=old['backtest']
    else:
        d=diagnostics(rows); b=backtest(rows)
    q.update(version=VERSION,data_sha256=key,backtest=b,diagnostics=d,prospective=summarize(q['distribution']),quality={'source':'單一月份 API；未獨立核對','invalid':bad,'conflicts':sorted(conflicts),'recent_missing':q['missing_recent'],'sync_error':sync_error,'historical_pending_legacy':len(h.get('pending_months',[])) if 'pending_months' in h else None,'note':'舊版待補月份數僅供參考；未核對特殊開獎日；雜湊不是第三方時間證明。'},conclusion='尚無證據證明五號全中或其他命中門檻優於公平隨機。')
    write(p,q);return q

if __name__=='__main__':
    err=None
    try:sync()
    except Exception as e:err=str(e);print('同步未完成，保留舊資料:',err)
    q=build(sync_error=err);print(q['message']);print('有效資料:',q['n'],'；歷史回測:',q['backtest']['model']['n'])
