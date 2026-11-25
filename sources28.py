from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs, urlencode
from urllib.request import urlopen, Request
from pathlib import Path
from html.parser import HTMLParser
from datetime import date
import os, re, webbrowser, json, time
from urllib.error import URLError, HTTPError

class Table(HTMLParser):
    def __init__(self):
        super().__init__(); self.rows=[]; self.row=None; self.cell=None
    def handle_starttag(self,tag,attrs):
        if tag=='tr': self.row=[]
        if tag=='td' and self.row is not None: self.cell=[]
    def handle_data(self,data):
        if self.cell is not None: self.cell.append(data)
    def handle_endtag(self,tag):
        if tag=='td' and self.cell is not None:
            self.row.append(''.join(self.cell).strip()); self.cell=None
        if tag=='tr' and self.row is not None:
            self.rows.append(self.row); self.row=None; self.cell=None

def parse_secondary(html):
    t=Table(); t.feed(html); result={}
    for r in t.rows:
        if len(r)<3 or not re.fullmatch(r'\d{6,12}',r[0]) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}',r[1]): continue
        if not re.fullmatch(r'\d{1,2}(?:\s*,\s*\d{1,2}){4}',r[2]): raise ValueError('secondary winning number format changed')
        d=date.fromisoformat(r[1]).isoformat(); n=sorted(map(int,r[2].split(',')))
        if len(set(n))!=5 or min(n)<1 or max(n)>39: raise ValueError('invalid secondary numbers')
        if d in result and result[d]!=n: raise ValueError('secondary duplicate conflict')
        result[d]=n
    if not result: raise ValueError('secondary table unavailable')
    return [{'d':d,'n':n} for d,n in sorted(result.items())]

def download(url):
    for attempt in range(3):
        try:
            with urlopen(Request(url,headers={'User-Agent':'Mozilla/5.0 (compatible; 539Research/40.1)'}),timeout=12) as r:
                body=r.read(80000001)
            if len(body)>80000000: raise ValueError('response too large')
            return body
        except (URLError, TimeoutError, OSError) as e:
            if isinstance(e, HTTPError) and e.code not in (408,429,500,502,503,504): raise
            if attempt==2: raise
            time.sleep(2**attempt)

import csv, io, zipfile, unicodedata
from urllib.parse import urlsplit
INDEX='https://gaze.nta.gov.tw/dntmb/OpenData/csvDw?ntaCode=D423F'
def decode_csv(raw):
    for enc in ('utf-8-sig','cp950','big5'):
        try: return raw.decode(enc)
        except UnicodeError: pass
    raise ValueError('unknown CSV encoding')
def norm(s): return re.sub(r'\s+','',unicodedata.normalize('NFKC',s))
def parse_archive(raw,year):
    found={}
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if sum(x.file_size for x in z.infolist())>150_000_000: raise ValueError('archive too large')
        for f in z.infolist():
            if not f.filename.lower().endswith('.csv'): continue
            if f.file_size>40_000_000: raise ValueError('CSV too large')
            a=list(csv.reader(io.StringIO(decode_csv(z.read(f)))))
            if not a: continue
            h=list(map(norm,a[0])); game=next((i for i,x in enumerate(h) if x in ('遊戲名稱','遊戲','彩種')),None)
            named=bool(re.search(r'今彩539|daily539|(^|[^0-9])539([^0-9]|$)',f.filename,re.I))
            if game is None and not named: continue
            if game is not None and not any(len(r)>game and norm(r[game]) in ('今彩539','539') for r in a[1:]): continue
            di=h.index('開獎日期'); ni=[next(i for i,x in enumerate(h) if x in (f'獎號{k}',f'號碼{k}',f'開出順序{k}',f'大小順序{k}')) for k in range(1,6)]
            for r in a[1:]:
                if not any(r): continue
                if game is not None and norm(r[game]) not in ('今彩539','539'): continue
                v=re.split(r'[-/.年月日]+',norm(r[di]).rstrip('日')); y,m,d=map(int,v); y=y+1911 if y<1911 else y
                dt=date(y,m,d).isoformat(); n=sorted(int(r[i]) for i in ni)
                if y!=year or len(set(n))!=5 or min(n)<1 or max(n)>39: raise ValueError('invalid archive record')
                if dt in found and found[dt]!=n: raise ValueError('archive conflict '+dt)
                found[dt]=n
    if not found: raise ValueError('no 539 CSV found')
    return [{'d':d,'n':n} for d,n in sorted(found.items())]
def annual(year):
    a=list(csv.reader(io.StringIO(decode_csv(download(INDEX)))))
    links=[]
    for r in a:
        if not any(norm(x).rstrip('年度年') in (str(year),str(year-1911)) for x in r): continue
        for x in r:
            u=urlsplit(x.strip()); host=u.hostname or ''
            if u.scheme=='https' and (host.endswith('.taiwanlottery.com') or host.endswith('.gov.tw') or host=='lotto.ctbcbank.com'): links.append(x.strip())
    if not links: raise ValueError('official index has no matching year')
    errors=[]
    for url in dict.fromkeys(links):
        try: return {'rows':parse_archive(download(url),year),'source':url}
        except Exception as e: errors.append(str(e))
    raise ValueError('; '.join(errors))

