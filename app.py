
import streamlit as st
import pandas as pd
import sqlite3, json
from pathlib import Path
from datetime import date, datetime

try:
    import yfinance as yf
except Exception:
    yf = None

DB = Path("investment_data.db")
DEFAULT_PASSWORD = "1688"

DEFAULT_HOLDINGS = [
("富邦銀行｜退休帳戶","退休長期","TW","TWD","00947","台新臺灣IC設計動能ETF",1004,25.78,25.78),
("富邦銀行｜退休帳戶","退休長期","US","USD","SOXQ","Invesco費城半導體ETF",2,94.685,94.685),
("富邦銀行｜退休帳戶","現金","CASH","TWD","CASH_FUBON","富邦退休戶現金",1,0,0),
("國泰銀行｜價差帳戶","價差操作","TW","TWD","1310","台苯",1000,9.52,9.52),
("國泰銀行｜價差帳戶","核心長期","TW","TWD","2330","台積電",20,1778.5,1778.5),
("國泰銀行｜價差帳戶","現金","CASH","TWD","CASH_CATHAY","國泰價差戶現金",1,0,0),
("永豐銀行｜核心帳戶","核心長期","TW","TWD","00631L","元大台灣50正2",4070,26.66,38.33),
("永豐銀行｜核心帳戶","價差操作","TW","TWD","00830","國泰費城半導體ETF",1056,81.77,81.77),
("永豐銀行｜核心帳戶","價差操作","TW","TWD","2302","麗正",1000,19.53,19.53),
("永豐銀行｜核心帳戶","核心長期","TW","TWD","2330","台積電",510,489.14,1778.5),
("永豐銀行｜核心帳戶","價差操作","TW","TWD","2337","旺宏",1000,149.71,149.71),
("永豐銀行｜核心帳戶","價差操作","TW","TWD","2408","南亞科",200,227.32,227.32),
("永豐銀行｜核心帳戶","價差操作","TW","TWD","3491","昇達科",5,1557.2,1557.2),
("永豐銀行｜核心帳戶","價差操作","TW","TWD","6116","彩晶",3000,10.31,10.31),
("永豐銀行｜核心帳戶","價差操作","TW","TWD","6558","興能高",2000,36,36),
("永豐銀行｜核心帳戶","價差操作","TW","TWD","6603","富強鑫",1000,26.64,26.64),
("永豐銀行｜核心帳戶","價差操作","TW","TWD","6770","力積電",1000,63.79,63.79),
("永豐銀行｜核心帳戶","核心長期","US","USD","NVDA","NVIDIA",1,142.95,142.95),
("永豐銀行｜核心帳戶","退休長期","US","USD","QQQ","Invesco QQQ",1.55011,645.15,645.15),
("永豐銀行｜核心帳戶","現金","CASH","TWD","CASH_SINOPAC","永豐核心戶現金",1,0,0),
]

st.set_page_config(page_title="投資總控 Pro v4 Professional", page_icon="💼", layout="wide")
st.markdown("""
<style>
.stApp{background:#F8F5EF}.block-container{padding-top:1rem;padding-bottom:4rem}
[data-testid="stMetric"]{background:#FFFDF8;padding:16px;border-radius:18px;border:1px solid #E8E0D0;box-shadow:0 4px 14px rgba(0,0,0,.05)}
section[data-testid="stSidebar"]{background:#F3EEE4} h1,h2,h3{color:#4B443C}
.stButton>button,.stDownloadButton>button{background:#D9C8A9;color:white;border:none;border-radius:15px;font-weight:700}
</style>
""", unsafe_allow_html=True)

def con(): return sqlite3.connect(DB)

def init_db():
    c=con(); cur=c.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS holdings(
    id INTEGER PRIMARY KEY AUTOINCREMENT, account TEXT,purpose TEXT,market TEXT,currency TEXT,
    symbol TEXT,name TEXT,shares REAL,cost REAL,price REAL,last_update TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS trade_logs(
    id INTEGER PRIMARY KEY AUTOINCREMENT,log_date TEXT,account TEXT,symbol TEXT,action TEXT,note TEXT,
    qty REAL DEFAULT 0,price REAL DEFAULT 0,buy_fee REAL DEFAULT 0,sell_fee REAL DEFAULT 0,
    tax REAL DEFAULT 0,realized_profit REAL DEFAULT 0,cash_flow REAL DEFAULT 0,
    auto_update_inventory INTEGER DEFAULT 1,fee_auto INTEGER DEFAULT 1)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS daily_assets(
    id INTEGER PRIMARY KEY AUTOINCREMENT,record_date TEXT UNIQUE,total_asset REAL,total_cost REAL,
    total_profit REAL,realized_profit REAL DEFAULT 0,unrealized_profit REAL DEFAULT 0,total_fee REAL DEFAULT 0,cash_total REAL DEFAULT 0)""")
    # add missing columns for old DB
    cur.execute("PRAGMA table_info(trade_logs)"); cols=[x[1] for x in cur.fetchall()]
    for col,typ in {"qty":"REAL DEFAULT 0","price":"REAL DEFAULT 0","buy_fee":"REAL DEFAULT 0","sell_fee":"REAL DEFAULT 0","tax":"REAL DEFAULT 0","realized_profit":"REAL DEFAULT 0","cash_flow":"REAL DEFAULT 0","auto_update_inventory":"INTEGER DEFAULT 1","fee_auto":"INTEGER DEFAULT 1"}.items():
        if col not in cols: cur.execute(f"ALTER TABLE trade_logs ADD COLUMN {col} {typ}")
    cur.execute("SELECT COUNT(*) FROM holdings")
    if cur.fetchone()[0]==0:
        for h in DEFAULT_HOLDINGS:
            cur.execute("""INSERT INTO holdings(account,purpose,market,currency,symbol,name,shares,cost,price,last_update)
            VALUES(?,?,?,?,?,?,?,?,?,?)""", (*h,"預設"))
    c.commit(); c.close()

def load(table, order="id DESC"):
    c=con(); df=pd.read_sql_query(f"SELECT * FROM {table} ORDER BY {order}",c); c.close(); return df
def load_holdings():
    c=con(); df=pd.read_sql_query("SELECT * FROM holdings",c); c.close(); return df
def save_holdings(df):
    c=con(); df.to_sql("holdings",c,if_exists="replace",index=False); c.close()

def add_log(log_date, account, symbol, action, note, qty, price, buy_fee, sell_fee, tax, realized_profit, cash_flow, auto_update_inventory, fee_auto):
    c=con(); cur=c.cursor()
    cur.execute("""INSERT INTO trade_logs(log_date,account,symbol,action,note,qty,price,buy_fee,sell_fee,tax,realized_profit,cash_flow,auto_update_inventory,fee_auto)
    VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",(log_date,account,symbol,action,note,qty,price,buy_fee,sell_fee,tax,realized_profit,cash_flow,1 if auto_update_inventory else 0,1 if fee_auto else 0))
    c.commit(); c.close()

def save_daily(total_asset,total_cost,total_profit,realized,unrealized,fee,cash):
    c=con(); cur=c.cursor(); d=date.today().isoformat()
    cur.execute("""INSERT INTO daily_assets(record_date,total_asset,total_cost,total_profit,realized_profit,unrealized_profit,total_fee,cash_total)
    VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(record_date) DO UPDATE SET total_asset=excluded.total_asset,total_cost=excluded.total_cost,total_profit=excluded.total_profit,realized_profit=excluded.realized_profit,unrealized_profit=excluded.unrealized_profit,total_fee=excluded.total_fee,cash_total=excluded.cash_total""",(d,total_asset,total_cost,total_profit,realized,unrealized,fee,cash))
    c.commit(); c.close()

def password_ok():
    if "auth" not in st.session_state: st.session_state.auth=False
    if st.session_state.auth: return True
    st.title("💼 投資總控 Pro v4 Professional")
    pw=st.text_input("密碼",type="password")
    if st.button("登入"):
        try: real=st.secrets.get("APP_PASSWORD",DEFAULT_PASSWORD)
        except Exception: real=DEFAULT_PASSWORD
        if pw==real: st.session_state.auth=True; st.rerun()
        else: st.error("密碼錯誤")
    return False

def fetch_price(row):
    if yf is None or row["market"]=="CASH": return None
    sym=str(row["symbol"]).upper()
    tick=sym if row["market"]=="US" else sym+".TW"
    for t in [tick, sym+".TWO"]:
        try:
            hist=yf.Ticker(t).history(period="5d")
            if not hist.empty: return float(hist["Close"].dropna().iloc[-1])
        except Exception: pass
    return None

def fx_rate():
    if yf:
        try:
            h=yf.Ticker("TWD=X").history(period="5d")
            if not h.empty: return float(h["Close"].dropna().iloc[-1])
        except Exception: pass
    return 32.0

def calc(df, usd):
    df=df.copy()
    fx=df["currency"].map(lambda x: usd if x=="USD" else 1.0)
    df["台幣市值"]=df["shares"]*df["price"]*fx
    df["台幣成本"]=df["shares"]*df["cost"]*fx
    cash=df["market"].eq("CASH")
    df.loc[cash,"台幣市值"]=df.loc[cash,"price"]*fx[cash]
    df.loc[cash,"台幣成本"]=df.loc[cash,"cost"]*fx[cash]
    df["未實現損益"]=df["台幣市值"]-df["台幣成本"]
    df["報酬率"]=df["未實現損益"]/df["台幣成本"].replace(0,pd.NA)*100
    return df

def money(x):
    try: return f"{x:,.0f}"
    except Exception: return "0"

def is_etf(s):
    s=str(s).upper()
    return s.startswith(("00","006","007","008","009")) or s in ["QQQ","SMH","SOXQ","VOO","SPY","SOXX"]
def fees(market,symbol,action,qty,price,discount,min_fee):
    amt=float(qty)*float(price); bf=sf=tax=0
    if market=="TW" and amt>0:
        f=max(round(amt*0.001425*discount), int(min_fee))
        if action in ["買進","加碼"]: bf=f
        if action in ["賣出","停利","停損"]:
            sf=f; tax=round(amt*(0.001 if is_etf(symbol) else 0.003))
    return bf,sf,tax

def cash_symbol(account):
    if "國泰" in account: return "CASH_CATHAY"
    if "永豐" in account: return "CASH_SINOPAC"
    if "富邦" in account: return "CASH_FUBON"
    return "CASH_OTHER"
def update_cash(account, amount, currency="TWD"):
    df=load_holdings(); sym=cash_symbol(account); m=df["symbol"].eq(sym)
    if m.any():
        i=df[m].index[0]; df.loc[i,"price"]=float(df.loc[i,"price"])+float(amount); df.loc[i,"cost"]=df.loc[i,"price"]
    else:
        df=pd.concat([df,pd.DataFrame([{"id":None,"account":account,"purpose":"現金","market":"CASH","currency":currency,"symbol":sym,"name":account+"現金","shares":1.0,"cost":float(amount),"price":float(amount),"last_update":datetime.now().strftime("%Y-%m-%d %H:%M")}])],ignore_index=True)
    save_holdings(df)

def apply_trade(account,purpose,market,currency,symbol,name,action,qty,price,bf,sf,tax):
    if qty<=0 or price<=0: return 0
    df=load_holdings(); symbol=symbol.upper().strip(); m=(df["account"].eq(account)) & (df["symbol"].str.upper().eq(symbol))
    amount=qty*price; rp=0.0
    if action in ["買進","加碼"]:
        total=amount+bf
        if m.any():
            i=df[m].index[0]; oldq=float(df.loc[i,"shares"]); oldc=float(df.loc[i,"cost"])
            newq=oldq+qty; df.loc[i,"shares"]=newq; df.loc[i,"cost"]=((oldq*oldc)+total)/newq; df.loc[i,"price"]=price
        else:
            df=pd.concat([df,pd.DataFrame([{"id":None,"account":account,"purpose":purpose,"market":market,"currency":currency,"symbol":symbol,"name":name or symbol,"shares":qty,"cost":total/qty,"price":price,"last_update":datetime.now().strftime("%Y-%m-%d %H:%M")}])],ignore_index=True)
        save_holdings(df); update_cash(account,-(amount+bf),currency)
    elif action in ["賣出","停利","停損"] and m.any():
        i=df[m].index[0]; oldq=float(df.loc[i,"shares"]); oldc=float(df.loc[i,"cost"])
        sellq=min(qty,oldq); rp=(price-oldc)*sellq
        df.loc[i,"shares"]=oldq-sellq; df.loc[i,"price"]=price
        save_holdings(df); update_cash(account, amount-sf-tax, currency)
    return rp

if not password_ok(): st.stop()
init_db()
df=load_holdings(); logs=load("trade_logs","log_date DESC,id DESC")

with st.sidebar:
    st.header("設定")
    usd=st.number_input("USD/TWD 匯率", value=float(fx_rate()), step=0.01)
    discount=st.number_input("台股手續費折扣", value=0.28, step=0.01)
    min_fee=st.number_input("最低手續費", value=1, step=1)
    if st.button("🔄 更新全部市價", use_container_width=True):
        pbar=st.progress(0)
        for i,row in df.iterrows():
            p=fetch_price(row)
            if p:
                df.loc[i,"price"]=p; df.loc[i,"last_update"]=datetime.now().strftime("%Y-%m-%d %H:%M")
            pbar.progress((i+1)/len(df))
        save_holdings(df); st.success("市價更新完成"); st.rerun()

dfv=calc(df,usd)
realized=logs["realized_profit"].fillna(0).sum() if not logs.empty else 0
total_fee=(logs["buy_fee"].fillna(0).sum()+logs["sell_fee"].fillna(0).sum()+logs["tax"].fillna(0).sum()) if not logs.empty else 0
net_realized=realized-total_fee
total_asset=dfv["台幣市值"].sum(); total_cost=dfv["台幣成本"].sum(); unreal=dfv["未實現損益"].sum()
cash=dfv.loc[dfv["purpose"].eq("現金"),"台幣市值"].sum()
total_profit=unreal+net_realized

st.title("💼 投資總控 Pro v4 Professional｜純投資修正版")
h=df[df["symbol"].str.upper()=="00631L"]
if not h.empty:
    p=float(h.iloc[0]["price"]); sh=float(h.iloc[0]["shares"])
    if p<39: st.info(f"今日建議：00631L 目前 {p:.2f}，距離 39 元還差 {39-p:.2f} 元。")
    elif p<44: st.info(f"今日建議：00631L 已到第一批區間，可評估賣出約 {int(sh*0.2)} 股。")
    elif p<50: st.info(f"今日建議：00631L 已到第二批區間，可評估再賣出約 {int(sh*0.2)} 股。")
    else: st.info("今日建議：00631L 已到第三批以上區間，可評估分批鎖定獲利。")

c1,c2,c3,c4=st.columns(4)
c1.metric("目前總資產",money(total_asset)+" 元")
c2.metric("未實現損益",money(unreal)+" 元")
c3.metric("已實現損益淨額",money(net_realized)+" 元")
c4.metric("現金部位",money(cash)+" 元")
c5,c6,c7,c8=st.columns(4)
c5.metric("總成本",money(total_cost)+" 元")
c6.metric("總損益估算",money(total_profit)+" 元")
c7.metric("累計手續費/稅",money(total_fee)+" 元")
c8.metric("報酬率",f"{(total_profit/total_cost*100 if total_cost else 0):.2f}%")

if st.button("📌 儲存今日資產紀錄", use_container_width=True):
    save_daily(total_asset,total_cost,total_profit,net_realized,unreal,total_fee,cash); st.success("已儲存")

backup={"holdings":df.to_dict("records"),"trade_logs":logs.to_dict("records"),"daily_assets":load("daily_assets","record_date DESC").to_dict("records")}
st.download_button("⬇️ 匯出備份 JSON", json.dumps(backup,ensure_ascii=False,indent=2), "投資總控備份.json", "application/json", use_container_width=True)

tabs=st.tabs(["總覽","快速交易","持股管理","00631L操作","交易紀錄","每日資產","損益分析","資產配置","退休中心","備份還原"])

with tabs[0]:
    st.subheader("各帳戶金額")
    acct=dfv.groupby("account")[["台幣市值","台幣成本","未實現損益"]].sum().reset_index()
    acct["報酬率"]=acct["未實現損益"]/acct["台幣成本"].replace(0,pd.NA)*100
    st.dataframe(acct,use_container_width=True,hide_index=True)
    st.subheader("用途分類")
    pur=dfv.groupby("purpose")[["台幣市值","台幣成本","未實現損益"]].sum().reset_index()
    pur["報酬率"]=pur["未實現損益"]/pur["台幣成本"].replace(0,pd.NA)*100
    st.dataframe(pur,use_container_width=True,hide_index=True)

with tabs[1]:
    st.subheader("快速交易：自動更新庫存、平均成本、現金")
    with st.form("quick_trade"):
        a,b,c=st.columns(3)
        tdate=a.date_input("交易日期",value=date.today())
        account=b.selectbox("帳戶",sorted(df["account"].unique()))
        action=c.selectbox("動作",["買進","賣出","加碼","停利","停損","現金轉入","現金轉出"])
        d,e,f=st.columns(3)
        sym=d.text_input("股票代碼",value="00631L").upper()
        name=e.text_input("名稱",value="")
        purpose=f.selectbox("用途",["價差操作","核心長期","退休長期","現金"])
        g,i,j=st.columns(3)
        market=g.selectbox("市場",["TW","US","CASH"])
        currency=i.selectbox("幣別",["TWD","USD"])
        qty=j.number_input("股數/數量",value=0.0,step=1.0)
        k,l,m=st.columns(3)
        price=k.number_input("成交價",value=0.0,step=0.01)
        auto_fee=l.checkbox("自動計算手續費/稅",value=True)
        auto_inv=m.checkbox("自動更新庫存與現金",value=True)
        abf,asf,atax=fees(market,sym,action,qty,price,discount,min_fee)
        n,o,p=st.columns(3)
        bf=n.number_input("買進手續費",value=float(abf if auto_fee else 0),step=1.0)
        sf=o.number_input("賣出手續費",value=float(asf if auto_fee else 0),step=1.0)
        tax=p.number_input("證交稅/交易稅",value=float(atax if auto_fee else 0),step=1.0)
        cash_flow=st.number_input("現金流入/流出（轉入正數、轉出負數；買賣股票可留0）",value=0.0,step=1.0)
        note=st.text_area("備註")
        if st.form_submit_button("新增交易並更新"):
            rp=0.0
            if action in ["現金轉入","現金轉出"]: update_cash(account,cash_flow,currency)
            elif auto_inv: rp=apply_trade(account,purpose,market,currency,sym,name,action,qty,price,bf,sf,tax)
            add_log(tdate.isoformat(),account,sym,action,note,qty,price,bf,sf,tax,rp,cash_flow,auto_inv,auto_fee)
            st.success("已新增交易"); st.rerun()

with tabs[2]:
    st.subheader("持股總表")
    cols=["id","account","purpose","market","currency","symbol","name","shares","cost","price","台幣市值","台幣成本","未實現損益","報酬率","last_update"]
    edited=st.data_editor(dfv[cols],use_container_width=True,num_rows="dynamic",hide_index=True)
    if st.button("💾 儲存持股修改"):
        save_holdings(edited[["id","account","purpose","market","currency","symbol","name","shares","cost","price","last_update"]])
        st.success("已儲存"); st.rerun()

with tabs[3]:
    st.subheader("00631L 分批獲利計畫")
    tgt=df[df["symbol"].str.upper()=="00631L"]
    if tgt.empty: st.warning("找不到00631L")
    else:
        h=tgt.iloc[0]; a,b,c,d=st.columns(4)
        sp=[a.number_input("第一批賣出價",value=39.0,step=.1),b.number_input("第二批賣出價",value=44.0,step=.1),c.number_input("第三批賣出價",value=50.0,step=.1)]
        ratio=d.number_input("每批賣出比例%",value=20.0,step=1.0)/100
        sell_sh=int(h["shares"]*ratio); remain=h["shares"]; rows=[]; alloc=[]
        for idx,x in enumerate(sp,1):
            _,sf,t=fees("TW","00631L","賣出",sell_sh,x,discount,min_fee)
            gross=sell_sh*(x-h["cost"]); net=gross-sf-t; remain-=sell_sh
            rows.append({"批次":f"第{idx}批","目標價":x,"賣出股數":sell_sh,"賣出金額":sell_sh*x,"預估毛獲利":gross,"預估費稅":sf+t,"預估淨獲利":net,"剩餘股數":remain,"狀態":"已達標" if h["price"]>=x else "未達標"})
            alloc.append({"批次":f"第{idx}批","淨獲利":net,"QQQ 30%":net*.3,"SMH 20%":net*.2,"保留現金 30%":net*.3,"價差戶 20%":net*.2})
        st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
        st.subheader("獲利分配"); st.dataframe(pd.DataFrame(alloc),use_container_width=True,hide_index=True)

with tabs[4]:
    st.subheader("交易紀錄")
    ls=load("trade_logs","log_date DESC,id DESC")
    if not ls.empty:
        ls["淨已實現損益"]=ls["realized_profit"].fillna(0)-ls["buy_fee"].fillna(0)-ls["sell_fee"].fillna(0)-ls["tax"].fillna(0)
        kw=st.text_input("搜尋交易紀錄")
        if kw: ls=ls[ls.astype(str).apply(lambda col: col.str.contains(kw,case=False,na=False)).any(axis=1)]
    st.dataframe(ls,use_container_width=True,hide_index=True)

with tabs[5]:
    st.subheader("每日資產變化")
    daily=load("daily_assets","record_date DESC")
    if daily.empty: st.info("尚未有每日資產紀錄")
    else:
        daily["較前次變化"]=daily["total_asset"].diff(-1)
        st.dataframe(daily,use_container_width=True,hide_index=True)
        ch=daily.sort_values("record_date")
        st.line_chart(ch.set_index("record_date")[[c for c in ["total_asset","unrealized_profit","realized_profit","cash_total"] if c in ch.columns]])

with tabs[6]:
    st.subheader("損益分析")
    l2=load("trade_logs","log_date DESC,id DESC")
    if l2.empty: st.info("尚未有交易紀錄")
    else:
        l2["淨已實現損益"]=l2["realized_profit"].fillna(0)-l2["buy_fee"].fillna(0)-l2["sell_fee"].fillna(0)-l2["tax"].fillna(0)
        l2["月份"]=pd.to_datetime(l2["log_date"]).dt.to_period("M").astype(str)
        l2["年度"]=pd.to_datetime(l2["log_date"]).dt.year.astype(str)
        for name,grp in [("依標的","symbol"),("依帳戶","account"),("依月份","月份"),("依年度","年度")]:
            st.write(name); st.dataframe(l2.groupby(grp)[["realized_profit","buy_fee","sell_fee","tax","淨已實現損益"]].sum().reset_index(),use_container_width=True,hide_index=True)

with tabs[7]:
    st.subheader("資產配置")
    st.write("依帳戶"); st.bar_chart(dfv.groupby("account")["台幣市值"].sum())
    st.write("依用途"); st.bar_chart(dfv.groupby("purpose")["台幣市值"].sum())
    st.write("前十大持股")
    top=dfv[dfv["purpose"]!="現金"].sort_values("台幣市值",ascending=False).head(10)
    st.dataframe(top[["symbol","name","account","purpose","台幣市值","未實現損益","報酬率"]],use_container_width=True,hide_index=True)

with tabs[8]:
    st.subheader("退休中心")
    ret=dfv[dfv["purpose"].isin(["退休長期","核心長期"])]
    st.dataframe(ret[["account","symbol","name","shares","cost","price","台幣市值","未實現損益","報酬率"]],use_container_width=True,hide_index=True)
    monthly=st.number_input("每月持續投入金額",value=5000.0,step=1000.0)
    ar=st.number_input("假設年化報酬率 %",value=10.0,step=1.0)/100
    cur=ret["台幣市值"].sum(); rows=[]
    for y in [5,10,15,20,25,30]:
        r=ar/12; n=y*12
        fv=cur*((1+ar)**y)+monthly*(((1+r)**n-1)/r if r else n)
        rows.append({"年數":y,"預估資產":fv})
    st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)

with tabs[9]:
    st.subheader("備份 / 還原")
    up=st.file_uploader("上傳備份 JSON 還原",type=["json"])
    if up is not None and st.button("確認還原"):
        data=json.load(up); c=con()
        for table,key in [("holdings","holdings"),("trade_logs","trade_logs"),("daily_assets","daily_assets")]:
            if key in data: pd.DataFrame(data[key]).to_sql(table,c,if_exists="replace",index=False)
        c.commit(); c.close(); st.success("已還原，請重新整理頁面")
