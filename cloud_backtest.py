"""Chronological retrospective research; aggregate metrics only."""
import math, random, hashlib, json
from collections import Counter
P=65621/575757
BASE=5/39

def upper(k,n):
    if k==0:return 1.0
    logs=[math.lgamma(n+1)-math.lgamma(i+1)-math.lgamma(n-i+1)+i*math.log(P)+(n-i)*math.log1p(-P) for i in range(k,n+1)]
    m=max(logs);return min(1.,math.exp(m)*sum(math.exp(x-m) for x in logs))

def research(rows, progress=lambda p,m:None):
    from datetime import date
    n=len(rows)
    if not 300<=n<=10000:raise ValueError('需要300～10000期 SQLite 資料')
    dates=[x['d'] for x in rows]
    if dates!=sorted(set(dates)):raise ValueError('日期重複或順序錯誤')
    for x in rows:
        date.fromisoformat(x['d']); a=x['n']
        if len(a)!=5 or len(set(a))!=5 or any(type(v)!=int or not 1<=v<=39 for v in a):raise ValueError('獎號格式錯誤')
    warm=100; cut=warm+int((n-warm)*.8); r=random.Random(539)
    names=['隨機對照','長期頻率','近期加權','遺漏期數','貝氏全歷史','Logistic']
    stats={name:[0]*6 for name in names}; yearly={}; brier=0.; loss=0.; data=[]; cumulative=Counter()
    for i,x in enumerate(rows):
        if i%50==0:progress(int(35*i/cut) if i<cut else 85+int(14*(i-cut)/(n-cut)),"整理歷史特徵" if i<cut else "獨立測試")
        if i>=warm:
            h=rows[i-warm:i]; f=Counter(); recent=Counter(); gap=[warm]*40; weight=[0.]*40
            for j,row in enumerate(h):
                for v in row['n']:
                    f[v]+=1;gap[v]=warm-1-j;weight[v]+=math.exp(-gap[v]/20)
                    if j>=90:recent[v]+=1
            features=[[1,f[v]/20,recent[v]/2,gap[v]/100,int(gap[v]==0)] for v in range(1,40)]
            y=[int(v in x['n']) for v in range(1,40)]
            if i<cut:data.extend(zip(features,y))
            else:
                if i==cut:
                    w=[math.log(5/34),0,0,0,0]
                    for epoch in range(30):
                        progress(35+int(50*epoch/30),f"Logistic 訓練 {epoch+1}/30")
                        g=[0.]*5
                        for a,b in data:
                            p=1/(1+math.exp(-(w[0]*a[0]+w[1]*a[1]+w[2]*a[2]+w[3]*a[3]+w[4]*a[4])))
                            for j in range(5):g[j]+=(p-b)*a[j]
                        w=[v-.5*(g[j]/len(data)+(.01*v if j else 0)) for j,v in enumerate(w)]
                    data.clear()
                probs=[1/(1+math.exp(-sum(t*u for t,u in zip(w,a)))) for a in features]
                brier+=sum((p-b)**2 for p,b in zip(probs,y));loss-=sum(b*math.log(p)+(1-b)*math.log1p(-p) for p,b in zip(probs,y))
                top=lambda key: sorted(range(1,40),key=lambda v:(-key(v),v))[:5]
                sets=[r.sample(range(1,40),5),top(lambda v:f[v]),top(lambda v:weight[v]),top(lambda v:gap[v]),top(lambda v:(100*BASE+cumulative[v])/(100+i)),top(lambda v:probs[v-1])]
                year=x['d'][:4]; block=yearly.setdefault(year,{'n':0,'hits':{name:0 for name in names}});block['n']+=1
                for name,s in zip(names,sets):
                    k=len(set(s)&set(x['n']));stats[name][k]+=1;block['hits'][name]+=int(k>=2)
        cumulative.update(x['n'])
    N=n-cut; results=[]
    for name,c in stats.items():
        k=sum(c[2:]); p=k/N; z=1.95996398454; den=1+z*z/N; mid=(p+z*z/(2*N))/den; rad=z*math.sqrt(p*(1-p)/N+z*z/(4*N*N))/den; pv=upper(k,N)
        results.append(dict(name=name,counts=c,rate=p,ci=[max(0,mid-rad),min(1,mid+rad)],p=pv,adjusted=min(1,pv*len(names))))
    gaps=[{'from':a,'to':b,'days':(date.fromisoformat(b)-date.fromisoformat(a)).days} for a,b in zip(dates,dates[1:]) if (date.fromisoformat(b)-date.fromisoformat(a)).days>3]
    return dict(version='26.0',total=n,first=dates[0],last=dates[-1],train=cut-warm,test=N,testFrom=dates[cut],testTo=dates[-1],baseline=P,results=results,yearly=yearly,logisticBrier=brier/(39*N),logisticLogLoss=loss/(39*N),baselineBrier=BASE*(1-BASE),baselineLogLoss=-BASE*math.log(BASE)-(1-BASE)*math.log1p(-BASE),gaps=gaps,sha256=hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(',',':')).encode()).hexdigest(),limitations='SQLite 來源未逐筆認證；日期間隔僅供檢查，不能證明完整。歷史保留集不是前瞻盲測。固定參數、六項 Bonferroni 校正；不提供投注號碼。')
