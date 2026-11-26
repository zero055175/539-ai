"""Standalone descriptive statistics and fixed research samples; no forecast claims."""
import json, os, time, hashlib
from collections import Counter
from datetime import datetime, date, timedelta, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from math import comb
TZ=timezone(timedelta(hours=8)); ROOT=Path(__file__).resolve().parent/'docs/data'
BASE=sum(comb(5,k)*comb(34,5-k) for k in range(2,6))/comb(39,5)
def read(p,default):
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else default
def write(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True); t=p.with_suffix('.tmp'); t.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8'); os.replace(t,p)
def clean(rows,today):
    by={}; bad=0; conflicts=set()
    for r in rows:
        try:
            d=r['d']; n=r['n']; dt=date.fromisoformat(d)
            if d!=dt.isoformat() or not date(2007,1,1)<=dt<=today or len(n)!=5 or len(set(n))!=5 or any(type(v)!=int or not 1<=v<=39 for v in n): raise ValueError()
            n=sorted(n)
            if d in by and by[d]!=n: conflicts.add(d)
            by[d]=n
        except (ValueError,TypeError,KeyError): bad+=1
    for d in conflicts: by.pop(d,None)
    return by,bad,conflicts
def fetch(month):
    url='https://api.taiwanlottery.com/TLCAPIWeB/Lottery/Daily539Result?'+urlencode(dict(period='',month=month,pageNum=1,pageSize=50))
    for i in range(2):
        try:
            with urlopen(Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=12) as r: j=json.loads(r.read(2000000))
            c=j['content']; a=c['daily539Res']
            if not isinstance(a,list) or int(c.get('totalSize',len(a)))>len(a): raise ValueError('資料分頁不完整')
            return [dict(d=str(x['lotteryDate'])[:10].replace('/','-'),n=sorted(map(int,x.get('drawNumberSize') or x['drawNumberAppear']))) for x in a]
        except Exception:
            if i: raise
            time.sleep(1)
def sync(root=ROOT,now=None,fetcher=fetch):
    now=(now or datetime.now(TZ)).astimezone(TZ); today=now.date(); p=root/'history.json'; old=read(p,{'rows':[]}); by,bad,conflicts=clean(old['rows'],today)
    # Never overwrite a corrupt existing archive automatically.
    if bad or conflicts: raise ValueError('原始歷史檔有異常，保留原檔，請檢查')
    months=[f'{y}-{m:02}' for y in range(2007,today.year+1) for m in range(1,(today.month if y==today.year else 12)+1)]
    recent=months[-5:][::-1]; done=set(old.get('lite_checked_months',[])); pending=[m for m in reversed(months) if m not in done and m not in recent]; cursor=int(old.get('lite_cursor',0)); rotated=pending[cursor%len(pending):]+pending[:cursor%len(pending)] if pending else []
    errors=[]; ok=[]
    for m in recent+rotated[:4]:
        try:
            raw=fetcher(m); a,b,c=clean(raw,today)
            if b or c or any(not d.startswith(m) for d in a) or (not a and m!=months[-1]): raise ValueError('月份資料異常或空白')
            if any(d in by and by[d]!=n for d,n in a.items()): raise ValueError('與既有資料衝突，保留舊資料')
            by.update(a); ok.append(m)
            if m!=months[-1]: done.add(m)
        except Exception as e: errors.append(f'{m}: {str(e)[:200]}')
    old.update(version='41.0',rows=[{'d':d,'n':n} for d,n in sorted(by.items())],updated_at=now.isoformat(),errors=errors,lite_checked_months=sorted(done),lite_cursor=cursor+min(4,len(rotated)),lite_sync={'ok':ok,'attempted':len(recent)+min(4,len(rotated)),'source':'原有月份 API；未獨立核對'})
    write(p,old); return old
def counts(rows): return {str(n):sum(n in r['n'] for r in rows) for n in range(1,40)}
def report(root=ROOT,now=None):
    now=(now or datetime.now(TZ)).astimezone(TZ); today=now.date(); day=today.isoformat(); h=read(root/'history.json',{'rows':[]}); by,bad,conflicts=clean(h['rows'],today); rows=[{'d':d,'n':n} for d,n in sorted(by.items())]; past=[r for r in rows if r['d']<day]; p=root/'lite41.json'; old=read(p,{'samples':[]}); samples=old['samples']; prev=today-timedelta(days=1)
    while prev.weekday()==6: prev-=timedelta(days=1)
    for r in samples:
        if r['date'] in by: r['hits']=len(set(r['numbers'])&set(by[r['date']])); r['actual']=by[r['date']]
    windows={str(w):{'n':len(rows[-w:]),'counts':counts(rows[-w:]),'start':rows[-w:][0]['d'] if rows else None} for w in (10,30,60,100)}
    missing=[(prev-timedelta(days=i)).isoformat() for i in range(14) if (prev-timedelta(days=i)).weekday()!=6 and (prev-timedelta(days=i)).isoformat() not in by]
    if any(r['date']==day for r in samples): msg='今日研究樣本已保存，不重選'
    elif today.weekday()==6 or now.hour>=19 or day in by: msg='非預設開獎日、已過研究截止或已有當日結果'
    elif bad or conflicts: msg='資料格式或衝突異常，暫停樣本'
    elif len(past)<10 or not past or past[-1]['d']!=prev.isoformat(): msg='至少需要10筆有效資料及前一預設開獎日資料'
    elif missing: msg='近14日有預設開獎日缺漏，暫停樣本；統計仍可用'
    else:
        a=past[-100:]; c=counts(a); nums=sorted(sorted(range(1,40),key=lambda n:(-c[str(n)],n))[:5]); samples.append({'date':day,'created_at':now.isoformat(),'numbers':nums,'n':len(a),'start':a[0]['d'],'end':a[-1]['d'],'hits':None,'history_sha256':hashlib.sha256(json.dumps(a,sort_keys=True).encode()).hexdigest()}); msg='今日固定頻率研究樣本已保存（非預測優勢）'
    scored=[r for r in samples if r.get('hits') is not None]; q={'version':'41.0','updated_at':now.isoformat(),'history_updated_at':h.get('updated_at'),'n':len(rows),'latest':rows[-1]['d'] if rows else None,'windows':windows,'all_counts':counts(rows),'invalid':bad,'conflicts':sorted(conflicts),'errors':h.get('errors',[]),'sync':h.get('lite_sync',{}),'missing_recent':missing,'message':msg,'samples':samples,'baseline':BASE,'scored':len(scored),'at_least_2':sum(r['hits']>=2 for r in scored),'distribution':[sum(r['hits']==k for r in scored) for k in range(6)]}; write(p,q); return q
if __name__=='__main__':
    try: sync()
    except Exception as e: print('同步未完成，保留舊資料:',e)
    print(report()['message'])
