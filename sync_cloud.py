"""Fetch historical public records; publish validated snapshots, not forecasts."""
import json, os, time
from pathlib import Path
from datetime import datetime, date, timezone, timedelta
from urllib.parse import urlencode
from sources28 import annual, download, parse_secondary
PATH=Path(__file__).resolve().parent/'docs/data/history.json'
TZ=timezone(timedelta(hours=8))
def monthly(m, today):
    j=json.loads(download('https://api.taiwanlottery.com/TLCAPIWeB/Lottery/Daily539Result?'+urlencode(dict(period='',month=m,pageNum=1,pageSize=50))))
    c=j['content']; a=c['daily539Res']
    if not isinstance(a,list) or int(c.get('totalSize',len(a)))>len(a): raise ValueError('invalid pagination')
    return [dict(d=str(x['lotteryDate'])[:10].replace('/','-'),n=sorted(map(int,x.get('drawNumberSize') or x['drawNumberAppear']))) for x in a]
def merge(by, incoming, today, prefix=''):
    tmp=dict(by)
    for x in incoming:
        d=x['d']; n=x['n']; dt=date.fromisoformat(d)
        if dt.isoformat()!=d or not date(2007,1,1)<=dt<=today or not d.startswith(prefix) or len(n)!=5 or len(set(n))!=5 or any(type(v)!=int or not 1<=v<=39 for v in n): raise ValueError('invalid row '+d)
        n=sorted(n)
        if d in tmp and tmp[d]!=n: raise ValueError('conflict '+d)
        tmp[d]=n
    return tmp
def main():
    now=datetime.now(TZ); today=now.date(); old=json.loads(PATH.read_text()); by=merge({},old['rows'],today); errors=[]; completed=set(old.get('completed_months',[])); months=[f'{y}-{m:02}' for y in range(2007,today.year+1) for m in range(1,(today.month if y==today.year else 12)+1)]; recent=months[-2:]
    # Annual archives first, bounded per run; rotating unsuccessful years avoid starvation.
    years=[y for y in range(2007,today.year+1) if any(m.startswith(str(y)) and m not in completed for m in months)]
    cursor=int(old.get('year_cursor',0)); years=years[cursor%len(years):]+years[:cursor%len(years)] if years else []
    for y in years[:2]:
        try:
            a=annual(y)['rows']; by=merge(by,a,today,str(y)); present={x['d'][:7] for x in a}; completed.update(m for m in present if m not in recent)
        except Exception as e: errors.append(f'{y}: {e}')
    missing=[m for m in months if m not in completed and m not in recent]; mc=int(old.get('month_cursor',0)); missing=missing[mc%len(missing):]+missing[:mc%len(missing)] if missing else []
    for m in recent+missing[:8]:
        try:
            a=monthly(m,today)
            if not a: raise ValueError('empty month')
            by=merge(by,a,today,m)
            if m not in recent: completed.add(m)
        except Exception as e: errors.append(f'{m}: {e}')
        time.sleep(.25)
    try:
        other=parse_secondary(download('https://en.lottolyzer.com/history/taiwan/daily-cash-539/page/1/per-page/50/summary-view').decode('utf-8'))
        conflicts=[x['d'] for x in other if x['d'] in by and by[x['d']]!=x['n']]
        if conflicts: raise RuntimeError('cross-source conflict '+','.join(conflicts))
        secondary=f'一致 {sum(x["d"] in by for x in other)} 期；其餘未核對'
    except RuntimeError: raise
    except Exception as e: secondary='未核對：'+str(e)
    # Never publish new data if the two sources disagree.
    q=dict(version='28.0',updated_at=now.isoformat(),rows=[dict(d=d,n=n) for d,n in sorted(by.items())],completed_months=sorted(completed),pending_months=[m for m in months if m not in completed and m not in recent],errors=errors,secondary_status=secondary,year_cursor=cursor+2,month_cursor=mc+8)
    tmp=PATH.with_suffix('.tmp');tmp.write_text(json.dumps(q,ensure_ascii=False),encoding='utf-8');os.replace(tmp,PATH);print(f'{len(by)} records; {len(errors)} errors; {secondary}')
if __name__=='__main__': main()
