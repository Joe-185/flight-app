import streamlit as st
import pandas as pd
from datetime import date, timedelta

# ==================== 頁面設定 ====================
st.set_page_config(
    page_title="✈️ 機票查詢系統",
    page_icon="✈️",
    layout="wide"
)

# ==================== 模擬資料 ====================
@st.cache_data
def load_flights():
    return pd.DataFrame([
        {"航班": "BR189", "航空公司": "長榮航空", "出發": "TPE", "抵達": "NRT", "起飛": "08:30", "降落": "12:45", "艙等": "經濟", "票價": 12500, "剩餘座位": 12},
        {"航班": "CI100", "航空公司": "中華航空", "出發": "TPE", "抵達": "NRT", "起飛": "09:15", "降落": "13:30", "艙等": "經濟", "票價": 11800, "剩餘座位": 5},
        {"航班": "JL802", "航空公司": "日本航空", "出發": "TPE", "抵達": "NRT", "起飛": "14:20", "降落": "18:35", "艙等": "經濟", "票價": 13200, "剩餘座位": 20},
        {"航班": "BR196", "航空公司": "長榮航空", "出發": "TPE", "抵達": "NRT", "起飛": "18:50", "降落": "23:05", "艙等": "商務", "票價": 45000, "剩餘座位": 3},
        {"航班": "BR125", "航空公司": "長榮航空", "出發": "KHH", "抵達": "HKG", "起飛": "07:50", "降落": "09:40", "艙等": "經濟", "票價": 8500, "剩餘座位": 18},
        {"航班": "CI918", "航空公司": "中華航空", "出發": "KHH", "抵達": "HKG", "起飛": "13:10", "降落": "15:00", "艙等": "經濟", "票價": 8200, "剩餘座位": 9},
        {"航班": "BR857", "航空公司": "長榮航空", "出發": "TPE", "抵達": "SIN", "起飛": "23:55", "降落": "04:30", "艙等": "經濟", "票價": 18500, "剩餘座位": 7},
        {"航班": "SQ879", "航空公司": "新加坡航空", "出發": "TPE", "抵達": "SIN", "起飛": "10:30", "降落": "15:10", "艙等": "經濟", "票價": 19200, "剩餘座位": 15},
        {"航班": "CI753", "航空公司": "中華航空", "出發": "TPE", "抵達": "SIN", "起飛": "16:40", "降落": "21:20", "艙等": "商務", "票價": 52000, "剩餘座位": 4},
        {"航班": "BR761", "航空公司": "長榮航空", "出發": "KHH", "抵達": "BKK", "起飛": "09:20", "降落": "12:10", "艙等": "經濟", "票價": 9800, "剩餘座位": 22},
    ])

# ==================== 標題 ====================
st.title("✈️ 機票查詢系統")
st.markdown("快速搜尋、比價，找到最適合你的航班 🛫")
st.divider()

# ==================== 側邊欄 ====================
with st.sidebar:
    st.header("🔍 搜尋條件")
    airports = ["TPE (台北桃園)", "KHH (高雄)", "NRT (東京成田)", 
                "HKG (香港)", "SIN (新加坡)", "BKK (曼谷)"]
    origin = st.selectbox("🛫 出發地", airports, index=0)
    destination = st.selectbox("🛬 目的地", airports, index=2)
    depart_date = st.date_input("📅 出發日期", 
                                 value=date.today() + timedelta(days=7),
                                 min_value=date.today())
    trip_type = st.radio("🎫 行程類型", ["單程", "來回"], horizontal=True)
    if trip_type == "來回":
        return_date = st.date_input("📅 回程日期",
                                     value=depart_date + timedelta(days=7),
                                     min_value=depart_date)
    adults = st.number_input("👥 成人人數", min_value=1, max_value=9, value=1)
    cabin = st.selectbox("💺 艙等", ["全部", "經濟", "商務"])
    sort_by = st.selectbox("📊 排序方式", ["票價（低→高）", "票價（高→低）", "起飛時間"])
    search_btn = st.button("🔎 搜尋航班", type="primary", use_container_width=True)

# ==================== 主畫面 ====================
df = load_flights()

if search_btn:
    origin_code = origin.split()[0]
    dest_code = destination.split()[0]
    results = df[(df["出發"] == origin_code) & (df["抵達"] == dest_code)].copy()
    
    if cabin != "全部":
        results = results[results["艙等"] == cabin]
    
    if sort_by == "票價（低→高）":
        results = results.sort_values("票價")
    elif sort_by == "票價（高→低）":
        results = results.sort_values("票價", ascending=False)
    else:
        results = results.sort_values("起飛")
    
    if results.empty:
        st.warning("❌ 查無符合條件的航班，請調整搜尋條件")
    else:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("✈️ 航班數量", f"{len(results)} 班")
        col2.metric("💰 最低票價", f"NT$ {results['票價'].min():,}")
        col3.metric("💎 最高票價", f"NT$ {results['票價'].max():,}")
        col4.metric("📊 平均票價", f"NT$ {int(results['票價'].mean()):,}")
        
        st.divider()
        st.subheader(f"🎯 搜尋結果（{origin_code} → {dest_code}）")
        
        for _, row in results.iterrows():
            total_price = row["票價"] * adults
            with st.container(border=True):
                c1, c2, c3, c4, c5 = st.columns([1.5, 2, 2, 1.5, 1.5])
                with c1:
                    st.markdown(f"**{row['航空公司']}**")
                    st.caption(f"航班 {row['航班']}")
                with c2:
                    st.markdown(f"🛫 **{row['起飛']}**")
                    st.caption(f"{row['出發']} 出發")
                with c3:
                    st.markdown(f"🛬 **{row['降落']}**")
                    st.caption(f"{row['抵達']} 抵達")
                with c4:
                    st.markdown(f"💺 {row['艙等']}艙")
                    st.caption(f"剩餘 {row['剩餘座位']} 位")
                with c5:
                    st.markdown(f"### NT$ {total_price:,}")
                    st.caption(f"{adults} 位旅客")
        
        st.divider()
        csv = results.to_csv(index=False).encode("utf-8-sig")
        st.download_button("📥 下載查詢結果 (CSV)",
                           data=csv,
                           file_name=f"flights_{origin_code}_{dest_code}_{depart_date}.csv",
                           mime="text/csv")
        
        with st.expander("📈 票價分析圖表"):
            st.bar_chart(results.set_index("航班")["票價"])
else:
    st.info("👈 請在左側選擇搜尋條件，然後點擊「搜尋航班」")
    with st.expander("👀 查看所有可用航班"):
        st.dataframe(df, use_container_width=True, hide_index=True)