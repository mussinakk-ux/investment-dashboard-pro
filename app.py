import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date
from pathlib import Path

try:
    import yfinance as yf
except Exception:
    yf = None

DB_PATH = Path("investment_data.db")
DEFAULT_PASSWORD = "1688"

DEFAULT_HOLDINGS = [
    {"account":"富邦銀行｜退休帳戶","purpose":"退休長期","market":"TW","currency":"TWD","symbol":"00947","name":"台新臺灣IC設計動能ETF","shares":1004.0,"cost":25.78,"price":25.78},
    {"account":"富邦銀行｜退休帳戶","purpose":"退休長期","market":"US","currency":"USD","symbol":"SOXQ","name":"Invesco費城半導體ETF","shares":2.0,"cost":94.685,"price":94.685},
    {"account":"國泰銀行｜價差帳戶","purpose":"價差操作","market":"TW","currency":"TWD","symbol":"1310","name":"台苯","shares":1000.0,"cost":9.52,"price":9.52},
    {"account":"國泰銀行｜價差帳戶","purpose":"核心長期","market":"TW","currency":"TWD","symbol":"2330","name":"台積電","shares":20.0,"cost":1778.5,"price":1778.5},
    {"account":"永豐銀行｜核心帳戶","purpose":"核心長期","market":"TW","currency":"TWD","symbol":"00631L","name":"元大台灣50正2","shares":4070.0,"cost":26.66,"price":38.33},
    {"account":"永豐銀行｜核心帳戶","purpose":"價差操作","market":"TW","currency":"TWD","symbol":"00830","name":"國泰費城半導體ETF","shares":1056.0,"cost":81.77,"price":81.77},
    {"account":"永豐銀行｜核心帳戶","purpose":"價差操作","market":"TW","currency":"TWD","symbol":"2302","name":"麗正","shares":1000.0,"cost":19.53,"price":19.53},
    {"account":"永豐銀行｜核心帳戶","purpose":"核心長期","market":"TW","currency":"TWD","symbol":"2330","name":"台積電","shares":510.0,"cost":489.14,"price":1778.5},
    {"account":"永豐銀行｜核心帳戶","purpose":"價差操作","market":"TW","currency":"TWD","symbol":"2337","name":"旺宏","shares":1000.0,"cost":149.71,"price":149.71},
    {"account":"永豐銀行｜核心帳戶","purpose":"價差操作","market":"TW","currency":"TWD","symbol":"2408","name":"南亞科","shares":200.0,"cost":227.32,"price":227.32},
    {"account":"永豐銀行｜核心帳戶","purpose":"價差操作","market":"TW","currency":"TWD","symbol":"3491","name":"昇達科","shares":5.0,"cost":1557.20,"price":1557.20},
    {"account":"永豐銀行｜核心帳戶","purpose":"價差操作","market":"TW","currency":"TWD","symbol":"6116","name":"彩晶","shares":3000.0,"cost":10.31,"price":10.31},
    {"account":"永豐銀行｜核心帳戶","purpose":"價差操作","market":"TW","currency":"TWD","symbol":"6558","name":"興能高","shares":2000.0,"cost":36.0,"price":36.0},
    {"account":"永豐銀行｜核心帳戶","purpose":"價差操作","market":"TW","currency":"TWD","symbol":"6603","name":"富強鑫","shares":1000.0,"cost":26.64,"price":26.64},
    {"account":"永豐銀行｜核心帳戶","purpose":"價差操作","market":"TW","currency":"TWD","symbol":"6770","name":"力積電","shares":1000.0,"cost":63.79,"price":63.79},
    {"account":"永豐銀行｜核心帳戶","purpose":"核心長期","market":"US","currency":"USD","symbol":"NVDA","name":"NVIDIA","shares":1.0,"cost":142.95,"price":142.95},
    {"account":"永豐銀行｜核心帳戶","purpose":"退休長期","market":"US","currency":"USD","symbol":"QQQ","name":"Invesco QQQ","shares":1.55011,"cost":645.15,"price":645.15},
]

st.set_page_config(page_title="投資總控 Pro", page_icon="💼", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
.stApp { background: #F8F5EF; }
.block-container { padding-top: 1rem; padding-bottom: 4rem; }
[data-testid="stMetric"] { background: #FFFDF8; padding: 18px; border-radius: 20px; border: 1px solid #E8E0D0; box-shadow: 0 4px 14px rgba(0,0,0,0.05); }
section[data-testid="stSidebar"] { background: #F3EEE4; }
div[data-testid="stDataFrame"] { background: #FFFDF8; border-radius: 16px; }
h1 { color: #4B443C; font-weight: 800; }
h2 { color: #5A5248; }
h3 { color: #6B6258; }
p, label, span { color: #5A5248; }
.stTabs [data-baseweb="tab-list"] { gap: 8px; }
.stTabs [data-baseweb="tab"] { background: #FFFDF8; border-radius: 999px; padding: 9px 18px; color: #5A5248; border: 1px solid #E8E0D0; }
.stTabs [aria-selected="true"] { background: #EADCC4 !important; color: #3F382F !important; }
.stButton > button { background: #D9C8A9; color: white; border: none; border-radius: 15px; font-weight: 700; padding: 0.6rem 1rem; }
.stButton > button:hover { background: #CDB894; color: white; border: none; }
.stDownloadButton > button { background: #C8B28A; color: white; border: none; border-radius: 15px; font-weight: 700; }
.stDownloadButton > button:hover { background: #B89E74; color: white; }
input, textarea, select { border-radius: 12px !important; }
div[data-testid="stAlert"] { border-radius: 15px; }
@media (max-width: 768px) { .block-container { padding-left: 0.8rem; padding-right: 0.8rem; } }
</style>
""", unsafe_allow_html=True)

def app_password():
    try:
        return st.secrets.get("APP_PASSWORD", DEFAULT_PASSWORD)
    except Exception:
        return DEFAULT_PASSWORD

def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if st.session_state.authenticated:
        return True
    st.title("💼 投資總控 Pro")
    st.info("請輸入密碼後使用。預設密碼是 1688，上雲端後建議到 Streamlit Secrets 修改。")
    pw = st.text_input("密碼", type="password")
    if st.button("登入"):
        if pw == app_password():
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("密碼錯誤")
    return False

def connect():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = connect()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS holdings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        account TEXT, purpose TEXT, market TEXT, currency TEXT,
        symbol TEXT, name TEXT, shares REAL, cost REAL, price REAL, last_update TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS daily_assets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        record_date TEXT UNIQUE,
        total_asset REAL, total_cost REAL, total_profit REAL
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS trade_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        log_date TEXT, account TEXT, symbol TEXT, action TEXT, note TEXT
    )
    """)
    cur.execute("SELECT COUNT(*) FROM holdings")
    if cur.fetchone()[0] == 0:
        for h in DEFAULT_HOLDINGS:
            cur.execute("""
            INSERT INTO holdings (account,purpose,market,currency,symbol,name,shares,cost,price,last_update)
            VALUES (?,?,?,?,?,?,?,?,?,?)
            """, (h["account"], h["purpose"], h["market"], h["currency"], h["symbol"], h["name"], h["shares"], h["cost"], h["price"], "預設"))
    conn.commit()
    conn.close()

def load_holdings():
    conn = connect()
    df = pd.read_sql_query("SELECT * FROM holdings", conn)
    conn.close()
    return df

def save_holdings(df):
    conn = connect()
    df.to_sql("holdings", conn, if_exists="replace", index=False)
    conn.close()

def save_daily_asset(total_asset, total_cost, total_profit):
    conn = connect()
    cur = conn.cursor()
    d = date.today().isoformat()
    cur.execute("""
    INSERT INTO daily_assets (record_date,total_asset,total_cost,total_profit)
    VALUES (?,?,?,?)
    ON CONFLICT(record_date) DO UPDATE SET
        total_asset=excluded.total_asset,
        total_cost=excluded.total_cost,
        total_profit=excluded.total_profit
    """, (d, total_asset, total_cost, total_profit))
    conn.commit()
    conn.close()

def load_daily():
    conn = connect()
    df = pd.read_sql_query("SELECT * FROM daily_assets ORDER BY record_date DESC", conn)
    conn.close()
    return df

def load_logs():
    conn = connect()
    df = pd.read_sql_query("SELECT * FROM trade_logs ORDER BY log_date DESC, id DESC", conn)
    conn.close()
    return df

def add_log(log_date, account, symbol, action, note):
    conn = connect()
    cur = conn.cursor()
    cur.execute("INSERT INTO trade_logs (log_date,account,symbol,action,note) VALUES (?,?,?,?,?)", (log_date, account, symbol, action, note))
    conn.commit()
    conn.close()

def yahoo_symbol(row):
    sym = str(row["symbol"]).upper().strip()
    if row["market"] == "US":
        return sym
    return f"{sym}.TW"

def fetch_price(row):
    if yf is None:
        return None
    try:
        data = yf.Ticker(yahoo_symbol(row)).history(period="5d")
        if not data.empty:
            return float(data["Close"].dropna().iloc[-1])
    except Exception:
        pass
    if row["market"] == "TW":
        try:
            sym = str(row["symbol"]).upper().strip()
            data = yf.Ticker(f"{sym}.TWO").history(period="5d")
            if not data.empty:
                return float(data["Close"].dropna().iloc[-1])
        except Exception:
            pass
    return None

def fetch_usd_twd():
    if yf is None:
        return 32.0
    try:
        data = yf.Ticker("TWD=X").history(period="5d")
        if not data.empty:
            return float(data["Close"].dropna().iloc[-1])
    except Exception:
        return 32.0
    return 32.0

def calc_values(df, usd_twd):
    df = df.copy()
    fx = df["currency"].map(lambda x: usd_twd if x == "USD" else 1.0)
    df["台幣市值"] = df["shares"] * df["price"] * fx
    df["台幣成本"] = df["shares"] * df["cost"] * fx
    df["損益"] = df["台幣市值"] - df["台幣成本"]
    df["報酬率"] = df["損益"] / df["台幣成本"] * 100
    return df

def money(x):
    return f"{x:,.0f}"

if not check_password():
    st.stop()

init_db()
df = load_holdings()

with st.sidebar:
    st.header("設定")
    usd_twd = st.number_input("USD/TWD 匯率", value=float(fetch_usd_twd()), step=0.01)
    st.caption("手機版可用 Safari / Chrome 開啟，並加入主畫面。")
    if st.button("🔄 更新全部市價", use_container_width=True):
        progress = st.progress(0)
        status = st.empty()
        updates = []
        for i, row in df.iterrows():
            p = fetch_price(row)
            if p:
                df.loc[i, "price"] = p
                df.loc[i, "last_update"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                updates.append(f"✅ {row['symbol']} → {p:.2f}")
            else:
                updates.append(f"⚠️ {row['symbol']} 抓不到，保留 {row['price']}")
            progress.progress((i + 1) / len(df))
        save_holdings(df)
        status.write("\n".join(updates))
        st.success("市價更新完成")
        st.rerun()

st.title("💼 投資總控 Pro｜雲端手機版")
st.caption("淡米白精品理財風格｜總資產・帳戶分流・00631L 操作・每日資產紀錄")

dfv = calc_values(df, usd_twd)
total_asset = dfv["台幣市值"].sum()
total_cost = dfv["台幣成本"].sum()
total_profit = total_asset - total_cost
total_return = total_profit / total_cost * 100 if total_cost else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("目前總資產", f"{money(total_asset)} 元")
c2.metric("總成本", f"{money(total_cost)} 元")
c3.metric("總損益", f"{money(total_profit)} 元")
c4.metric("總報酬率", f"{total_return:.2f}%")

colsave, colexport = st.columns(2)
with colsave:
    if st.button("📌 儲存今日資產紀錄", use_container_width=True):
        save_daily_asset(total_asset, total_cost, total_profit)
        st.success("已儲存今日資產紀錄")
with colexport:
    export_pack = {"holdings": df.to_dict(orient="records"), "daily_assets": load_daily().to_dict(orient="records"), "trade_logs": load_logs().to_dict(orient="records")}
    st.download_button("⬇️ 匯出備份 JSON", data=pd.Series(export_pack).to_json(force_ascii=False, indent=2), file_name="投資總控備份.json", mime="application/json", use_container_width=True)

tab1, tab2, tab3, tab4, tab5 = st.tabs(["帳戶總覽", "持股管理", "00631L操作", "每日資產", "交易紀錄"])

with tab1:
    st.subheader("各帳戶金額")
    acct = dfv.groupby("account")[["台幣市值", "台幣成本", "損益"]].sum().reset_index()
    acct["報酬率"] = acct["損益"] / acct["台幣成本"] * 100
    st.dataframe(acct, use_container_width=True, hide_index=True)
    st.subheader("用途分類")
    purpose = dfv.groupby("purpose")[["台幣市值", "台幣成本", "損益"]].sum().reset_index()
    purpose["報酬率"] = purpose["損益"] / purpose["台幣成本"] * 100
    st.dataframe(purpose, use_container_width=True, hide_index=True)

with tab2:
    st.subheader("持股總表")
    st.caption("可直接修改股數、成本、現價。新增持股可在表格最下方新增一列。")
    show_cols = ["id", "account", "purpose", "market", "currency", "symbol", "name", "shares", "cost", "price", "台幣市值", "台幣成本", "損益", "報酬率", "last_update"]
    edited = st.data_editor(dfv[show_cols], use_container_width=True, num_rows="dynamic", hide_index=True)
    if st.button("💾 儲存持股修改"):
        save_cols = ["id", "account", "purpose", "market", "currency", "symbol", "name", "shares", "cost", "price", "last_update"]
        save_holdings(edited[save_cols])
        st.success("已儲存持股資料")
        st.rerun()

with tab3:
    st.subheader("00631L 分批獲利計畫")
    target = df[df["symbol"].str.upper() == "00631L"]
    if target.empty:
        st.warning("找不到 00631L")
    else:
        h = target.iloc[0]
        colA, colB, colC, colD = st.columns(4)
        sell1 = colA.number_input("第一批賣出價", value=39.0, step=0.1)
        sell2 = colB.number_input("第二批賣出價", value=44.0, step=0.1)
        sell3 = colC.number_input("第三批賣出價", value=50.0, step=0.1)
        sell_ratio = colD.number_input("每批賣出比例 %", value=20.0, step=1.0) / 100
        sell_shares = int(h["shares"] * sell_ratio)
        remain = h["shares"]
        rows, alloc = [], []
        for n, sp in enumerate([sell1, sell2, sell3], start=1):
            amount = sell_shares * sp
            profit = sell_shares * (sp - h["cost"])
            remain -= sell_shares
            rows.append({"批次": f"第{n}批", "目標價": sp, "賣出股數": sell_shares, "賣出金額": amount, "實現獲利": profit, "剩餘股數": remain, "狀態": "已達標" if h["price"] >= sp else "未達標"})
            alloc.append({"批次": f"第{n}批", "獲利": profit, "QQQ 30%": profit * 0.3, "SMH 20%": profit * 0.2, "保留現金 30%": profit * 0.3, "價差戶 20%": profit * 0.2})
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        st.subheader("獲利分配")
        st.dataframe(pd.DataFrame(alloc), use_container_width=True, hide_index=True)
        next_rows = [r for r in rows if r["狀態"] == "未達標"]
        if next_rows:
            nr = next_rows[0]
            st.info(f"下一步：00631L 到 {nr['目標價']} 元，賣出 {nr['賣出股數']} 股。")
        else:
            st.success("三批目標都已達標，可設定 60 元以上第四批或轉入核心資產。")
        high = st.number_input("最近高點 / 下跌加碼參考價", value=50.0, step=0.1)
        buy_plan = pd.DataFrame([
            {"跌幅": "-10%", "參考價": high * 0.9, "動作": "投入保留現金 30%"},
            {"跌幅": "-15%", "參考價": high * 0.85, "動作": "再投入保留現金 30%"},
            {"跌幅": "-20%", "參考價": high * 0.8, "動作": "投入剩餘保留現金 40%"},
        ])
        st.subheader("下跌加碼計畫")
        st.dataframe(buy_plan, use_container_width=True, hide_index=True)

with tab4:
    st.subheader("每日資產變化")
    daily = load_daily()
    if not daily.empty:
        daily_show = daily.copy()
        daily_show["較前次變化"] = daily_show["total_asset"].diff(-1)
        st.dataframe(daily_show, use_container_width=True, hide_index=True)
        chart_df = daily.sort_values("record_date")
        st.line_chart(chart_df.set_index("record_date")["total_asset"])
    else:
        st.info("尚未有每日資產紀錄。")

with tab5:
    st.subheader("新增交易紀錄")
    with st.form("log_form"):
        ldate = st.date_input("日期", value=date.today())
        laccount = st.selectbox("帳戶", sorted(df["account"].unique()))
        lsymbol = st.text_input("標的", value="00631L")
        action = st.selectbox("動作", ["買進", "賣出", "加碼", "停利", "停損", "轉入長期帳戶", "轉入價差帳戶"])
        note = st.text_area("內容")
        submitted = st.form_submit_button("新增紀錄")
        if submitted:
            add_log(ldate.isoformat(), laccount, lsymbol, action, note)
            st.success("已新增交易紀錄")
            st.rerun()
    logs = load_logs()
    st.dataframe(logs, use_container_width=True, hide_index=True)
