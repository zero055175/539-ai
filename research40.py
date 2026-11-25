"""Unified research status, not a prediction or model selection engine."""
import json, hashlib, subprocess, sys
from pathlib import Path
from datetime import datetime, timezone
from research_cloud import write
from research38 import validate
from cloud_backtest import P
BASE=Path(__file__).resolve().parent
ROOT=BASE/'docs/data'
MODULES=[('30','research_cloud.py','reports/status.json'),('31','daily31.py','daily31.json'),('32','research32.py','benchmark32.json'),('33','research33.py','validation33.json'),('34','research34.py','prospective34.json'),('35','research35.py','inference35.json'),('36','research36.py','stability36.json'),('37','research37.py','audit37.json'),('38','research38.py','generalization38.json'),('39','research39.py','monitor39.json')]
def read(path):
    raw=path.read_bytes(); q=json.loads(raw)
    if not isinstance(q,dict):raise ValueError('report must be an object')
    return q,hashlib.sha256(raw).hexdigest()
def aggregate(root=ROOT, executions=None):
    executions=executions or {}; out=dict(version='40.0',checked_at=datetime.now(timezone.utc).isoformat(),baseline=P,modules=[],state='waiting',message='尚無足夠獨立證據',limitations='整合報告不等同獨立複驗。歷史完整性、特殊開獎日及第三方時間證明仍需核實；不依模型排名選號。')
    try:
        h,sha=read(root/'history.json');validate(h['rows']);out['history']=dict(n=len(h['rows']),latest=h['rows'][-1]['d'] if h['rows'] else None,sha256=sha,updated_at=h.get('updated_at'),pending=len(h.get('pending_months',[])),errors=len(h.get('errors',[])),secondary=h.get('secondary_status','未核對'))
    except (OSError,ValueError,KeyError,TypeError) as e:out['history']={'error':str(e)}
    for v,script,file in MODULES:
        item=dict(version=v,file=file,execution=executions.get(v,'not_run'))
        try:
            q,sha=read(root/file);item.update(state=q.get('state','reported'),message=q.get('message','報告可讀取'),checked_at=q.get('checked_at'),sha256=sha)
            if v=='35':out['inference']={'n':q.get('n',0),'target':q.get('target',300),'state':q.get('state'),'significant_count':sum(m.get('significant') is True for m in q.get('models',[]))}
            if v=='37':out['audit']=q.get('counts',{})
        except (OSError,ValueError,TypeError,AttributeError) as e:item.update(state='missing',message=str(e))
        out['modules'].append(item)
    h=out['history']; bad='error' in h or h.get('errors',0)>0 or any(x['execution']=='failed' or x['state'] in ('blocked','error') for x in out['modules'])
    if bad:out.update(state='blocked',message='研究流程有異常；不得解讀為預測優勢')
    elif h.get('n',0)<300 or h.get('pending',0) or any(x['execution']!='ok' or x['state'] in ('missing','waiting','insufficient','collecting') for x in out['modules']):out.update(state='waiting',message='資料、執行或獨立驗證尚不足')
    else:out.update(state='review',message='報告可供審查；仍未證實預測優勢')
    return out

def run():
    executions={}
    for v,script,file in MODULES:
        try:
            p=subprocess.run([sys.executable,str(BASE/script)],cwd=BASE,timeout=180)
            executions[v]='ok' if p.returncode==0 else 'failed'
        except (OSError,subprocess.TimeoutExpired):executions[v]='failed'
        print('V'+v,executions[v],flush=True)
    result=aggregate(ROOT,executions);write(ROOT/'integrated40.json',result);return result
if __name__=='__main__':
    r=run();print(r['message']);sys.exit(1 if any(x['execution']=='failed' for x in r['modules']) else 0)
