import streamlit as st
import pandas as pd
import sqlite3, json
from datetime import date, datetime
from pathlib import Path
try:
    import yfinance as yf
except Exception:
    yf=None

DB=Path('investment_data.db')
PWD='1688'
DEFAULT=[
('富邦銀行｜退休帳戶','退休長期','TW','TWD','00947','台新臺灣IC設計動能ETF',1004,25.78,25.78),('富邦銀行｜退休帳戶','退休長期','US','USD','SOXQ','Invesco費城半導體ETF',2,94.685,94.685),('富邦銀行｜退休帳戶','現金','CASH','TWD','CASH_FUBON','富邦退休戶現金',1,0,0),
('國泰銀行｜價差帳戶','價差操作','TW','TWD','1310','台苯',1000,9.52,9.52),('國泰銀行｜價差帳戶','核心長期','TW','TWD','2330','台積電',20,1778.5,1778.5),('國泰銀行｜價差帳戶','現金','CASH','TWD','CASH_CATHAY','國泰價差戶現金',1,0,0),
('永豐銀行｜核心帳戶','核心長期','TW','TWD','00631L','元大台灣50正2',4070,26.66,38.33),('永豐銀行｜核心帳戶','價差操作','TW','TWD','00830','國泰費城半導體ETF',1056,81.77,81.77),('永豐銀行｜核心帳戶','價差操作','TW','TWD','2302','麗正',1000,19.53,19.53),('永豐銀行｜核心帳戶','核心長期','TW','TWD','2330','台積電',510,489.14,1778.5),('永豐銀行｜核心帳戶','價差操作','TW','TWD','2337','旺宏',1000,149.71,149.71),('永豐銀行｜核心帳戶','價差操作','TW','TWD','2408','南亞科',200,227.32,227.32),('永豐銀行｜核心帳戶','價差操作','TW','TWD','3491','昇達科',5,1557.2,1557.2),('永豐銀行｜核心帳戶','價差操作','TW','TWD','6116','彩晶',3000,10.31,10.31),('永豐銀行｜核心帳戶','價差操作','TW','TWD','6558','興能高',2000,36,36),('永豐銀行｜核心帳戶','價差操作','TW','TWD','6603','富強鑫',1000,26.64,26.64),('永豐銀行｜核心帳戶','價差操作','TW','TWD','6770','力積電',1000,63.79,63.79),('永豐銀行｜核心帳戶','核心長期','US','USD','NVDA','NVIDIA',1,142.95,142.95),('永豐銀行｜核心帳戶','退休長期','US','USD','QQQ','Invesco QQQ',1.55011,645.15,645.15),('永豐銀行｜核心帳戶','現金','CASH','TWD','CASH_SINOPAC','永豐核心戶現金',1,0,0)]

st.set_page_config(page_title='投資總控 Pro v4 Professional',page_icon='💼',layout='wide',initial_sidebar_state='collapsed')
st.markdown('''<style>.stApp{background:#F8F5EF}.block-container{padding-top:1rem;padding-bottom:4rem}[data-testid="stMetric"]{background:#FFFDF8;padding:18px;border-radius:20px;border:1px solid #E8E0D0;box-shadow:0 4px 14px rgba(0,0,0,.05)}section[data-testid="stSidebar"]{background:#F3EEE4}h1{color:#4B443C}h2,h3,p,label,span{color:#5A5248}.stButton>button,.stDownloadButton>button{background:#D9C8A9;color:white;border:none;border-radius:15px;font-weight:700}.stTabs [data-baseweb="tab"]{background:#FFFDF8;border-radius:999px;padding:9px 18px;border:1px solid #E8E0D0}</style>''',unsafe_allow_html=True)

def conn(): return sqlite3.connect(DB)
def init():
    c=conn();cur=c.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS holdings(id INTEGER PRIMARY KEY AUTOINCREMENT,account TEXT,purpose TEXT,market TEXT,currency TEXT,symbol TEXT,name TEXT,shares REAL,cost REAL,price REAL,last_update TEXT)''')
    cur.execute('''CREATE TABLE IF NOT EXISTS trade_logs(id INTEGER PRIMARY KEY AUTOINCREMENT,log_date TEXT,account TEXT,symbol TEXT,action TEXT,note TEXT,qty REAL DEFAULT 0,price REAL DEFAULT 0,buy_fee REAL DEFAULT 0,sell_fee REAL DEFAULT 0,tax REAL DEFAULT 0,realized_profit REAL DEFAULT 0,cash_flow REAL DEFAULT 0,auto_update_inventory INTEGER DEFAULT 1,fee_auto INTEGER DEFAULT 1)''')
    cur.execute('''CREATE TABLE IF NOT EXISTS daily_assets(id INTEGER PRIMARY KEY AUTOINCREMENT,record_date TEXT UNIQUE,total_asset REAL,total_cost REAL,total_profit REAL,realized_profit REAL,unrealized_profit REAL,total_fee REAL,cash_total REAL)''')
    cur.execute('SELECT COUNT(*) FROM holdings')
    if cur.fetchone()[0]==0:
        for r in DEFAULT: cur.execute('INSERT INTO holdings(account,purpose,market,currency,symbol,name,shares,cost,price,last_update) VALUES(?,?,?,?,?,?,?,?,?,?)',(*r,'預設'))
    c.commit();c.close()

def read(t,order='id DESC'):
    c=conn();df=pd.read_sql_query(f'SELECT * FROM {t} ORDER BY {order}',c);c.close();return df
def holdings():
    c=conn();df=pd.read_sql_query('SELECT * FROM holdings',c);c.close();return df
def save_holdings(df):
    c=conn();df.to_sql('holdings',c,if_exists='replace',index=False);c.close()
def exec_sql(sql,p=()):
    c=conn();c.execute(sql,p);c.commit();c.close()

def password():
    try: return st.secrets.get('APP_PASSWORD',PWD)
    except Exception: return PWD
if 'ok' not in st.session_state: st.session_state.ok=False
if not st.session_state.ok:
    st.title('💼 投資總控 Pro v4 Professional')
    pw=st.text_input('密碼',type='password')
    if st.button('登入'):
        if pw==password(): st.session_state.ok=True;st.rerun()
        else: st.error('密碼錯誤')
    st.stop()

init(); df=holdings(); logs=read('trade_logs','log_date DESC,id DESC')

def ysym(r):
    s=str(r.symbol).upper().strip()
    if r.market=='US': return s
    if r.market=='CASH': return None
    return s+'.TW'
def fetch_price(r):
    if yf is None or r.market=='CASH': return None
    for sym in [ysym(r), str(r.symbol).upper().strip()+'.TWO']:
        try:
            d=yf.Ticker(sym).history(period='5d')
            if not d.empty: return float(d.Close.dropna().iloc[-1])
        except Exception: pass
    return None
def fxrate():
    if yf is None: return 32.0
    try:
        d=yf.Ticker('TWD=X').history(period='5d')
        if not d.empty: return float(d.Close.dropna().iloc[-1])
    except Exception: pass
    return 32.0

def calc(df,fx):
    d=df.copy(); f=d.currency.map(lambda x: fx if x=='USD' else 1.0)
    d['台幣市值']=d.shares*d.price*f; d['台幣成本']=d.shares*d.cost*f
    m=d.market.eq('CASH'); d.loc[m,'台幣市值']=d.loc[m,'price']*f[m]; d.loc[m,'台幣成本']=d.loc[m,'cost']*f[m]
    d['未實現損益']=d['台幣市值']-d['台幣成本']; d['報酬率']=d['未實現損益']/d['台幣成本'].replace(0,pd.NA)*100
    return d
def money(x): return f'{x:,.0f}'
def is_etf(s): return str(s).upper().startswith(('00','006','007','008','009')) or str(s).upper() in ['QQQ','SMH','SOXQ','VOO','SPY','SOXX']
def fees(market,symbol,action,qty,price,disc,min_fee):
    amt=qty*price; bf=sf=tax=0
    if market=='TW' and amt>0:
        fee=max(round(amt*0.001425*disc),int(min_fee))
        if action in ['買進','加碼']: bf=fee
        if action in ['賣出','停利','停損']:
            sf=fee; tax=round(amt*(0.001 if is_etf(symbol) else 0.003))
    return bf,sf,tax
def cash_sym(account):
    if '國泰' in account: return 'CASH_CATHAY'
    if '永豐' in account: return 'CASH_SINOPAC'
    if '富邦' in account: return 'CASH_FUBON'
    return 'CASH_OTHER'
def update_cash(account,amount,currency='TWD'):
    d=holdings(); sym=cash_sym(account); m=d.symbol.eq(sym)
    if m.any():
        i=d[m].index[0]; d.loc[i,'price']=float(d.loc[i,'price'])+amount; d.loc[i,'cost']=d.loc[i,'price']; d.loc[i,'last_update']=datetime.now().strftime('%Y-%m-%d %H:%M')
    else:
        d=pd.concat([d,pd.DataFrame([{'account':account,'purpose':'現金','market':'CASH','currency':currency,'symbol':sym,'name':account+'現金','shares':1,'cost':max(amount,0),'price':amount,'last_update':datetime.now().strftime('%Y-%m-%d %H:%M')}])],ignore_index=True)
    save_holdings(d)
def apply_trade(account,purpose,market,currency,symbol,name,action,qty,price,bf,sf,tax):
    if qty<=0 or price<=0: return 0
    d=holdings(); symbol=symbol.upper().strip(); m=(d.account.eq(account)) & (d.symbol.str.upper().eq(symbol)); amt=qty*price; realized=0
    if action in ['買進','加碼']:
        if m.any():
            i=d[m].index[0]; oq=float(d.loc[i,'shares']); oc=float(d.loc[i,'cost']); nq=oq+qty; nc=((oq*oc)+amt+bf)/nq if nq else price
            d.loc[i,['shares','cost','price','last_update']]=[nq,nc,price,datetime.now().strftime('%Y-%m-%d %H:%M')]
        else:
            nc=(amt+bf)/qty; d=pd.concat([d,pd.DataFrame([{'account':account,'purpose':purpose,'market':market,'currency':currency,'symbol':symbol,'name':name or symbol,'shares':qty,'cost':nc,'price':price,'last_update':datetime.now().strftime('%Y-%m-%d %H:%M')}])],ignore_index=True)
        save_holdings(d); update_cash(account,-(amt+bf),currency)
    elif action in ['賣出','停利','停損'] and m.any():
        i=d[m].index[0]; oq=float(d.loc[i,'shares']); oc=float(d.loc[i,'cost']); q=min(qty,oq); realized=(price-oc)*q
        d.loc[i,'shares']=oq-q; d.loc[i,'price']=price; d.loc[i,'last_update']=datetime.now().strftime('%Y-%m-%d %H:%M')
        save_holdings(d); update_cash(account,amt-sf-tax,currency)
    return realized

def realized_summary(logs):
    if logs.empty: return 0,0,0,0
    gross=logs.realized_profit.fillna(0).sum(); total_fee=logs.buy_fee.fillna(0).sum()+logs.sell_fee.fillna(0).sum()+logs.tax.fillna(0).sum(); tax=logs.tax.fillna(0).sum(); return gross,total_fee,tax,gross-total_fee

with st.sidebar:
    st.header('設定')
    fx=st.number_input('USD/TWD 匯率',value=float(fxrate()),step=0.01)
    disc=st.number_input('台股手續費折扣',value=0.28,step=0.01)
    min_fee=st.number_input('最低手續費',value=1,step=1)
    if st.button('🔄 更新全部市價',use_container_width=True):
        bar=st.progress(0); msg=[]; box=st.empty()
        for i,r in df.iterrows():
            p=fetch_price(r)
            if p: df.loc[i,'price']=p; df.loc[i,'last_update']=datetime.now().strftime('%Y-%m-%d %H:%M'); msg.append(f'✅ {r.symbol} → {p:.2f}')
            else: msg.append(f'⚠️ {r.symbol} 保留 {r.price}')
            bar.progress((i+1)/len(df))
        save_holdings(df); box.write('\n'.join(msg)); st.success('市價更新完成'); st.rerun()

dfv=calc(df,fx); gross,fee_total,tax_total,net_realized=realized_summary(logs)
total_asset=dfv['台幣市值'].sum(); total_cost=dfv['台幣成本'].sum(); unrealized=dfv['未實現損益'].sum(); cash=dfv.loc[dfv.purpose.eq('現金'),'台幣市值'].sum(); total_profit=unrealized+net_realized
st.title('💼 投資總控 Pro v4 Professional｜純投資版')

h=df[df.symbol.str.upper().eq('00631L')]
if not h.empty:
    p=float(h.iloc[0].price); sh=float(h.iloc[0].shares)
    if p<39: tip=f'00631L 目前 {p:.2f}，距離39元還差 {39-p:.2f} 元。'
    elif p<44: tip=f'00631L 已到第一批區間，可評估賣出約 {int(sh*0.2)} 股。'
    elif p<50: tip=f'00631L 已到第二批區間，可評估再賣出約 {int(sh*0.2)} 股。'
    else: tip='00631L 已到第三批以上區間，可評估分批鎖定獲利。'
    st.info('今日建議：'+tip)

c=st.columns(4); c[0].metric('目前總資產',money(total_asset)+' 元'); c[1].metric('未實現損益',money(unrealized)+' 元'); c[2].metric('已實現損益淨額',money(net_realized)+' 元'); c[3].metric('現金部位',money(cash)+' 元')
c=st.columns(4); c[0].metric('總成本',money(total_cost)+' 元'); c[1].metric('總損益估算',money(total_profit)+' 元'); c[2].metric('累計費稅',money(fee_total)+' 元'); c[3].metric('證交稅/交易稅',money(tax_total)+' 元')

if st.button('📌 儲存今日資產紀錄',use_container_width=True):
    exec_sql('''INSERT INTO daily_assets(record_date,total_asset,total_cost,total_profit,realized_profit,unrealized_profit,total_fee,cash_total) VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(record_date) DO UPDATE SET total_asset=excluded.total_asset,total_cost=excluded.total_cost,total_profit=excluded.total_profit,realized_profit=excluded.realized_profit,unrealized_profit=excluded.unrealized_profit,total_fee=excluded.total_fee,cash_total=excluded.cash_total''',(date.today().isoformat(),total_asset,total_cost,total_profit,net_realized,unrealized,fee_total,cash)); st.success('已儲存')
backup={'holdings':df.to_dict('records'),'trade_logs':logs.to_dict('records'),'daily_assets':read('daily_assets','record_date DESC').to_dict('records')}
st.download_button('⬇️ 匯出完整備份 JSON',json.dumps(backup,ensure_ascii=False,indent=2),'投資總控Pro_v4_Professional備份.json','application/json',use_container_width=True)

tabs=st.tabs(['總覽','快速交易','持股管理','00631L操作','交易紀錄','每日資產','損益分析','資產配置','退休中心','備份還原'])
with tabs[0]:
    st.subheader('各帳戶金額'); acct=dfv.groupby('account')[['台幣市值','台幣成本','未實現損益']].sum().reset_index(); acct['報酬率']=acct['未實現損益']/acct['台幣成本'].replace(0,pd.NA)*100; st.dataframe(acct,use_container_width=True,hide_index=True)
    st.subheader('用途分類'); pur=dfv.groupby('purpose')[['台幣市值','台幣成本','未實現損益']].sum().reset_index(); pur['報酬率']=pur['未實現損益']/pur['台幣成本'].replace(0,pd.NA)*100; st.dataframe(pur,use_container_width=True,hide_index=True)
with tabs[1]:
    st.subheader('快速交易：自動更新庫存、成本、現金')
    with st.form('trade'):
        a,b,c=st.columns(3); tdate=a.date_input('交易日期',value=date.today()); acc=b.selectbox('帳戶',sorted(df.account.unique())); action=c.selectbox('動作',['買進','賣出','加碼','停利','停損','現金轉入','現金轉出'])
        a,b,c=st.columns(3); sym=a.text_input('股票代碼',value='00631L').upper(); name=b.text_input('名稱'); purpose=c.selectbox('用途',['價差操作','核心長期','退休長期','現金'])
        a,b,c=st.columns(3); market=a.selectbox('市場',['TW','US','CASH']); curr=b.selectbox('幣別',['TWD','USD']); qty=c.number_input('股數/數量',value=0.0,step=1.0)
        a,b,c=st.columns(3); price=a.number_input('成交價',value=0.0,step=0.01); auto_fee=b.checkbox('自動計算手續費/稅',value=True); auto_inv=c.checkbox('自動更新庫存與現金',value=True)
        bf0,sf0,tax0=fees(market,sym,action,qty,price,disc,min_fee)
        a,b,c=st.columns(3); bf=a.number_input('買進手續費',value=float(bf0 if auto_fee else 0),step=1.0); sf=b.number_input('賣出手續費',value=float(sf0 if auto_fee else 0),step=1.0); tax=c.number_input('證交稅/交易稅',value=float(tax0 if auto_fee else 0),step=1.0)
        cash_flow=st.number_input('現金流入/流出（轉入正數、轉出負數；買賣可留0）',value=0.0,step=1.0); note=st.text_area('備註')
        if st.form_submit_button('新增交易並更新'):
            rp=0
            if action in ['現金轉入','現金轉出']: update_cash(acc,cash_flow,curr)
            elif auto_inv: rp=apply_trade(acc,purpose,market,curr,sym,name,action,qty,price,bf,sf,tax)
            add_log(tdate.isoformat(),acc,sym,action,note,qty,price,bf,sf,tax,rp,cash_flow,auto_inv,auto_fee); st.success('已新增交易'); st.rerun()
with tabs[2]:
    cols=['id','account','purpose','market','currency','symbol','name','shares','cost','price','台幣市值','台幣成本','未實現損益','報酬率','last_update']; ed=st.data_editor(dfv[cols],use_container_width=True,num_rows='dynamic',hide_index=True)
    if st.button('💾 儲存持股修改'):
        save_holdings(ed[['id','account','purpose','market','currency','symbol','name','shares','cost','price','last_update']]); st.success('已儲存'); st.rerun()
with tabs[3]:
    st.subheader('00631L 分批獲利計畫')
    h=df[df.symbol.str.upper().eq('00631L')]
    if h.empty: st.warning('找不到00631L')
    else:
        r=h.iloc[0]; a,b,c,d=st.columns(4); s1=a.number_input('第一批賣出價',39.0); s2=b.number_input('第二批賣出價',44.0); s3=c.number_input('第三批賣出價',50.0); ratio=d.number_input('每批賣出比例%',20.0)/100
        q=int(r.shares*ratio); remain=r.shares; rows=[]; alloc=[]
        for n,sp in enumerate([s1,s2,s3],1):
            bf,sf,tax=fees('TW','00631L','賣出',q,sp,disc,min_fee); gross=q*(sp-r.cost); net=gross-sf-tax; remain-=q
            rows.append({'批次':f'第{n}批','目標價':sp,'賣出股數':q,'賣出金額':q*sp,'預估毛獲利':gross,'預估費稅':sf+tax,'預估淨獲利':net,'剩餘股數':remain,'狀態':'已達標' if r.price>=sp else '未達標'})
            alloc.append({'批次':f'第{n}批','淨獲利':net,'QQQ 30%':net*.3,'SMH 20%':net*.2,'保留現金 30%':net*.3,'價差戶 20%':net*.2})
        st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True); st.subheader('獲利分配'); st.dataframe(pd.DataFrame(alloc),use_container_width=True,hide_index=True)
with tabs[4]:
    l=read('trade_logs','log_date DESC,id DESC')
    if not l.empty:
        l['淨已實現損益']=l.realized_profit.fillna(0)-l.buy_fee.fillna(0)-l.sell_fee.fillna(0)-l.tax.fillna(0); kw=st.text_input('搜尋交易紀錄')
        if kw: l=l[l.astype(str).apply(lambda col: col.str.contains(kw,case=False,na=False)).any(axis=1)]
    st.dataframe(l,use_container_width=True,hide_index=True)
with tabs[5]:
    d=read('daily_assets','record_date DESC')
    if not d.empty:
        d['較前次變化']=d.total_asset.diff(-1); st.dataframe(d,use_container_width=True,hide_index=True); st.line_chart(d.sort_values('record_date').set_index('record_date')[['total_asset','unrealized_profit','realized_profit','cash_total']])
    else: st.info('尚未有每日資產紀錄')
with tabs[6]:
    l=read('trade_logs','log_date DESC,id DESC')
    if not l.empty:
        l['淨已實現損益']=l.realized_profit.fillna(0)-l.buy_fee.fillna(0)-l.sell_fee.fillna(0)-l.tax.fillna(0); l['月份']=pd.to_datetime(l.log_date).dt.to_period('M').astype(str); l['年度']=pd.to_datetime(l.log_date).dt.year.astype(str)
        for label,key in [('依標的','symbol'),('依帳戶','account'),('依月份','月份'),('依年度','年度')]: st.write(label); st.dataframe(l.groupby(key)[['realized_profit','buy_fee','sell_fee','tax','淨已實現損益']].sum().reset_index(),use_container_width=True,hide_index=True)
    else: st.info('尚未有交易紀錄')
with tabs[7]:
    st.write('依帳戶'); st.bar_chart(dfv.groupby('account')['台幣市值'].sum()); st.write('依用途'); st.bar_chart(dfv.groupby('purpose')['台幣市值'].sum()); top=dfv[dfv.purpose!='現金'].sort_values('台幣市值',ascending=False).head(10); st.dataframe(top[['symbol','name','account','purpose','台幣市值','未實現損益','報酬率']],use_container_width=True,hide_index=True)
with tabs[8]:
    retire=dfv[dfv.purpose.isin(['退休長期','核心長期'])]; st.dataframe(retire[['account','symbol','name','shares','cost','price','台幣市值','未實現損益','報酬率']],use_container_width=True,hide_index=True)
    monthly=st.number_input('每月持續投入金額',5000.0,step=1000.0); ar=st.number_input('假設年化報酬率%',10.0,step=1.0)/100; cur=retire['台幣市值'].sum(); rows=[]
    for y in [5,10,15,20,25,30]:
        r=ar/12; n=y*12; fv=monthly*(((1+r)**n-1)/r) if r else monthly*n; rows.append({'年數':y,'預估資產':cur*((1+ar)**y)+fv})
    st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
with tabs[9]:
    up=st.file_uploader('上傳備份 JSON 還原',type=['json'])
    if up is not None and st.button('確認還原'):
        data=json.load(up); c=conn()
        for t,k in [('holdings','holdings'),('trade_logs','trade_logs'),('daily_assets','daily_assets')]:
            if k in data: pd.DataFrame(data[k]).to_sql(t,c,if_exists='replace',index=False)
        c.commit(); c.close(); st.success('已還原，請重新整理')
