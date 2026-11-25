"""Descriptive stability of verified prospective outcomes; no model selection."""
import json, statistics
from datetime import datetime, timezone
from research35 import report, wilson, ROOT, NAMES, P
from research_cloud import write
WINDOWS=(30,90,180,365)

def summarize(values):
    n=len(values); k=sum(x>=2 for x in values)
    return dict(n=n,k=k,rate=k/n if n else None,ci=wilson(k,n),mean_hits=sum(values)/n if n else None,counts=[values.count(i) for i in range(6)])

def stability(root=ROOT):
    out=dict(version='36.0',checked_at=datetime.now(timezone.utc).isoformat(),baseline=P,models=[],limitations='視窗為已核對期數而非日曆天數；重疊視窗僅描述統計，不作顯著性檢定或模型選擇。缺期可能造成偏差。')
    if not (root/'prospective34.json').exists():return dict(out,state='waiting',message='尚無前瞻性紀錄')
    try:
        check=report(root)
        if check['state']=='blocked':return dict(out,state='blocked',message=check['message'])
        records=json.loads((root/'prospective34.json').read_text())['records']; scored=[]
        for r in records:
            if r['state']!='scored':break
            scored.append(r)
        dates=[r['sealed']['date'] for r in scored]
        out.update(state='ready' if scored else 'waiting',message='描述性長期穩定性分析' if scored else '尚無已核對期數',n=len(scored),first=dates[0] if dates else None,last=dates[-1] if dates else None)
        for name in NAMES:
            values=[r['hits'][name] for r in scored]; windows=[]
            for w in WINDOWS:
                windows.append(dict(window=w,available=len(values)>=w,**(summarize(values[-w:]) if len(values)>=w else {})))
            blocks=[summarize(values[i:i+30]) for i in range(0,len(values)-29,30)]
            rates=[b['rate'] for b in blocks]; rolling=[sum(v>=2 for v in values[i:i+30])/30 for i in range(len(values)-29)]
            out['models'].append(dict(name=name,total=summarize(values),windows=windows,blocks30=blocks,block_sd=statistics.stdev(rates) if len(rates)>=2 else None,rolling_min=min(rolling) if rolling else None,rolling_max=max(rolling) if rolling else None))
        return out
    except (ValueError,KeyError,TypeError,OSError) as e:return dict(out,state='blocked',message='資料驗證失敗：'+str(e),models=[])

if __name__=='__main__':
    r=stability();write(ROOT/'stability36.json',r);print(r['message'])
