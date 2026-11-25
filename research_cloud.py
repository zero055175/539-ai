"""Automatic historical research archive; no forecast or recommended numbers."""
import json, hashlib, os
from pathlib import Path
from datetime import datetime, timezone
from cloud_backtest import research
ROOT=Path(__file__).resolve().parent/'docs/data'
def write(path,obj):
    tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(obj,ensure_ascii=False,allow_nan=False),encoding='utf-8');os.replace(tmp,path)
def run(root=ROOT):
    h=json.loads((root/'history.json').read_text()); rows=h['rows']; dest=root/'reports';dest.mkdir(exist_ok=True)
    idx=json.loads((dest/'index.json').read_text()); now=datetime.now(timezone.utc).isoformat()
    status=dict(version='30.0',checked_at=now,records=len(rows),pending_months=h.get('pending_months',[]),source_errors=h.get('errors',[]),secondary_status=h.get('secondary_status','未核對'))
    if len(rows)<300:
        status.update(state='insufficient',message='至少需要300期歷史資料');write(dest/'status.json',status);return status
    fingerprint=hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(',',':')).encode()).hexdigest(); key='v30-'+fingerprint
    reports=idx.get('reports',[])
    if any(r.get('id')==key for r in reports) and (dest/(key+'.json')).exists():
        status.update(state='unchanged',message='相同資料已完成研究',latest=key+'.json');write(dest/'status.json',status);return status
    try:
        result=research(rows); result.update(version='30.0',created_at=now,source_quality={k:status[k] for k in ('pending_months','source_errors','secondary_status')},kind='historical retrospective',source_verified=False)
        write(dest/(key+'.json'),result)
        reports=[r for r in reports if r.get('id')!=key]; reports.insert(0,dict(id=key,file=key+'.json',created_at=now,total=len(rows),test=result['test'],first=result['first'],last=result['last'],brier=result['logisticBrier'],baseline=result['baselineBrier']))
        write(dest/'index.json',dict(version='30.0',reports=reports,note='歷史研究；重疊測試集不是獨立證據'))
        status.update(state='complete',message='雲端歷史研究完成',latest=key+'.json');write(dest/'status.json',status);return status
    except Exception as e:
        status.update(state='error',message=str(e));write(dest/'status.json',status);raise
if __name__=='__main__': print(json.dumps(run(),ensure_ascii=False))
