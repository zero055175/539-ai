"""Aggregate research quality monitoring. No recommendations or model selection."""
import json, math
from pathlib import Path
from datetime import datetime, timezone
from research_cloud import write
from cloud_backtest import P
from research38 import validate
ROOT=Path(__file__).resolve().parent/'docs/data'

def monitor(root=ROOT):
    out=dict(version='39.0',checked_at=datetime.now(timezone.utc).isoformat(),baseline=P,checks=[],warnings=[],state='waiting',message='尚無足夠證據',limitations='描述性監測，不作連續顯著性檢定、不選擇模型。固定樣本檢定不能證明未來效果；第三方時間戳及完整期別仍需獨立確認。')
    def check(name,ok,detail):
        out['checks'].append(dict(name=name,ok=ok,detail=detail))
    def read(name):
        try:
            q=json.loads((root/name).read_text());check(name,True,'可讀取');return q
        except (OSError,ValueError):check(name,None,'缺少或無法讀取');return None
    h=read('history.json'); inf=read('inference35.json'); st=read('stability36.json'); au=read('audit37.json'); ge=read('generalization38.json')
    try:
        if h is not None:
            validate(h['rows']);check('歷史資料格式',True,str(len(h['rows']))+'期');check('同步狀態',not bool(h.get('errors') or h.get('pending_months')),'檢查來源錯誤與待同步月份')
        for label,q in [('固定檢定',inf),('穩定性',st),('泛化診斷',ge)]:
            if q is not None:check(label,False if q.get('state')=='blocked' else None if q.get('state') in ('waiting','insufficient','collecting') else True,q.get('state','unknown'))
        if au is not None:
            counts=au['counts']; bad=sum(counts.get(k,0) for k in ('invalid_seal','verification_failed','verified_late'));check('封存稽核',False if bad else True if counts.get('verified_before_cutoff',0)>0 and not counts.get('hash_only',0) else None,'異常 '+str(bad)+'；僅雜湊 '+str(counts.get('hash_only',0)))
        if ge and ge.get('result'):check('前綴一致性',bool(ge['result']['prefix_pass']),'僅限V38診斷模組')
        if st:
            for m in st.get('models',[]):
                w={x['window']:x for x in m['windows'] if x.get('available')}
                if 30 in w and 180 in w and w[30]['rate'] < w[180]['rate']-.05:out['warnings'].append('某模型近期30期較180期低逾5百分點；描述性警示，非失效證明。')
        if inf and inf.get('state')=='complete':out['fixed_test']='曾達名目校正門檻，仍須獨立複驗' if any(m.get('significant') for m in inf.get('models',[])) else '未達校正顯著門檻'
        else:out['fixed_test']='尚無完整固定樣本檢定'
    except (KeyError,TypeError,ValueError,AttributeError) as e:check('報告格式',False,str(e))
    if any(c['ok'] is False for c in out['checks']):out.update(state='blocked',message='研究品質異常，暫停證據解讀')
    elif any(c['ok'] is None for c in out['checks']):out.update(state='waiting',message='資料或時間證明不足')
    else:out.update(state='review',message='基本品質檢查通過；不代表預測有效')
    return out
if __name__=='__main__':
    r=monitor();write(ROOT/'monitor39.json',r);print(r['message'])
