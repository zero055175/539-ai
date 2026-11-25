"""Audit existing research seals; optional RFC3161 trusted timestamp service."""
import os,json,hashlib,subprocess,tempfile,urllib.request
from pathlib import Path
from datetime import datetime,timezone
from research34 import digest,TZ
from research_cloud import write
ROOT=Path(__file__).resolve().parent/'docs/data'
def cmd(*args):
    return subprocess.run(['openssl',*args],check=True,capture_output=True,text=True,timeout=20).stdout

def verify(data, token, ca, cutoff):
    with tempfile.TemporaryDirectory() as tmp:
        p=Path(tmp); (p/'data').write_bytes(data); (p/'token').write_bytes(token)
        cmd('ts','-verify','-data',str(p/'data'),'-in',str(p/'token'),'-CAfile',str(ca))
        info=cmd('ts','-reply','-in',str(p/'token'),'-text')
        line=next(x.split(': ',1)[1].strip() for x in info.splitlines() if x.startswith('Time stamp: '))
        t=datetime.strptime(line,'%b %d %H:%M:%S %Y GMT').replace(tzinfo=timezone.utc)
        return t.isoformat(),t<cutoff

def run(root=ROOT,now=None):
    now=now or datetime.now(TZ); q=json.loads((root/'prospective34.json').read_text()); folder=root/'timestamp37';folder.mkdir(exist_ok=True)
    ca=os.getenv('TSA_CA_FILE');url=os.getenv('TSA_URL'); entries=[]
    for r in q['records']:
        a=r['sealed'];d=a['date']; cutoff=datetime.fromisoformat(d+'T19:00:00+08:00'); sha=digest(a); data=sha.encode('ascii'); path=folder/(sha+'.tsr'); item={'date':d,'sha256':sha,'state':'hash_only'}
        if sha!=r['sha256'] or r['state']=='blocked':item['state']='invalid_seal'
        elif ca:
            try:
                if not path.exists() and url and now<cutoff and d==now.astimezone(TZ).date().isoformat():
                    with tempfile.TemporaryDirectory() as tmp:
                        p=Path(tmp);(p/'data').write_bytes(data);cmd('ts','-query','-data',str(p/'data'),'-sha256','-cert','-out',str(p/'query'))
                        req=urllib.request.Request(url,data=(p/'query').read_bytes(),headers={'Content-Type':'application/timestamp-query'})
                        with urllib.request.urlopen(req,timeout=15) as response:token=response.read(262145)
                        if len(token)>262144:raise ValueError('oversize response')
                        verify(data,token,ca,cutoff);path.write_bytes(token)
                if path.exists():
                    stamp,early=verify(data,path.read_bytes(),ca,cutoff);item.update(state='verified_before_cutoff' if early else 'verified_late',timestamp=stamp)
            except Exception as exc:item.update(state='verification_failed',error=type(exc).__name__)
        entries.append(item)
    result={'version':'37.0','checked_at':now.isoformat(),'configured':bool(ca and url),'records':entries,'counts':{s:sum(x['state']==s for x in entries) for s in ['hash_only','invalid_seal','verified_before_cutoff','verified_late','verification_failed']},'limitations':'RFC3161 須配置受信任 TSA 與 CA；未配置只核對雜湊，不能證明開獎前存在。19:00 為研究截止，非官方開獎時間。時間戳不證明模型有效或紀錄完整。'}
    write(root/'audit37.json',result);return result
if __name__=='__main__':print(run()['counts'])
