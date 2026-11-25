"""Frozen chronological holdout audit. No claim of prospective independence."""
import json, hashlib
from pathlib import Path
from datetime import datetime, timezone, date
from research32 import benchmark
from research_cloud import write
ROOT=Path(__file__).resolve().parent/'docs/data'
PROTOCOL='v33-fixed-nine-models-100-warm-80-20'
def digest(x):
    return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def run(root=ROOT):
    h=json.loads((root/'history.json').read_text(encoding='utf-8')); rows=h['rows']; dest=root/'validation33.json'; lock=root/'validation33_lock.json'
    now=datetime.now(timezone.utc).isoformat(); status=dict(version='33.0',checked_at=now,records=len(rows),protocol=PROTOCOL)
    def finish(state,message,**kw):
        status.update(state=state,message=message,**kw);write(dest,status);return status
    if lock.exists():
        a=json.loads(lock.read_text(encoding='utf-8')); n=a['total']; cut=a['cut']
        if a['protocol']!=PROTOCOL or a['code_sha256']!=code_hash():return finish('blocked','研究程式已變更；不可沿用原封存結論')
        if len(rows)<n or digest(rows[:n])!=a['data_sha256']:return finish('blocked','封存資料遭修改或新增較早資料；停止驗證')
        if digest(a['result'])!=a['result_sha256']:return finish('blocked','封存報告指紋不一致')
        return finish('complete','沿用固定歷史測試結果；新增資料不重複計入',lock=a)
    if len(rows)<300:return finish('insufficient','至少需要300期資料')
    if h.get('pending_months') or h.get('errors'):return finish('blocked','同步仍有缺漏月份或來源錯誤；暫不建立封存')
    dates=[date.fromisoformat(x['d']) for x in rows]
    if any((b-a).days>3 for a,b in zip(dates,dates[1:])):return finish('blocked','發現超過3日的資料間隔；需核對開獎日曆')
    r=benchmark(rows); n=len(rows); cut=n-r['test']; a=dict(protocol=PROTOCOL,created_at=now,total=n,cut=cut,train_end=rows[cut-1]['d'],test_start=rows[cut]['d'],test_end=rows[-1]['d'],data_sha256=digest(rows),train_sha256=digest(rows[:cut]),test_sha256=digest(rows[cut:]),code_sha256=code_hash(),result=r,result_sha256=digest(r),independence='historical_only',limitations='歷史資料可能已被V32或其他模型使用；不是真正未見資料。Git封存可被修改，非第三方時間戳。間隔檢查不證明完整。')
    write(lock,a);return finish('complete','固定歷史保留集已封存',lock=a)
def code_hash():
    return digest({n:hashlib.sha256(Path(__file__).with_name(n).read_bytes()).hexdigest() for n in ['research33.py','research32.py','cloud_backtest.py']})
if __name__=='__main__':print(run()['message'])
