import streamlit as st
import pandas as pd
from datetime import date, timedelta, datetime

# ==================== Try loading 3 APIs ====================
try:
    from fli.search import SearchFlights
    from fli.models import (
        FlightSearchFilters, FlightSegment, Airport,
        PassengerInfo, SeatType, MaxStops, SortBy
    )
    FLI_OK = True
except ImportError:
    FLI_OK = False

try:
    from fast_flights import FlightData, Passengers, get_flights
    FAST_OK = True
except ImportError:
    FAST_OK = False

try:
    from serpapi import GoogleSearch
    SERP_OK = True
except ImportError:
    SERP_OK = False

st.set_page_config(
    page_title="✈️ 機票查詢系統 - 三合一",
    page_icon="✈️",
    layout="wide"
)

AIRPORTS = {
    "TPE (台北桃園)": "TPE",
    "KHH (高雄)": "KHH",
    "TSA (台北松山)": "TSA",
    "NRT (東京成田)": "NRT",
    "HND (東京羽田)": "HND",
    "KIX (大阪關西)": "KIX",
    "ICN (首爾仁川)": "ICN",
    "HKG (香港)": "HKG",
    "SIN (新加坡)": "SIN",
    "BKK (曼谷)": "BKK",
    "LAX (洛杉矶)": "LAX",
    "JFK (紐約)": "JFK",
    "LHR (倫敦)": "LHR",
    "CDG (巴黎)": "CDG",
    "SYD (雪梨)": "SYD",
}


def format_duration(minutes):
    try:
        m = int(minutes)
        return f"{m // 60}h {m % 60}m"
    except Exception:
        return str(minutes)


def format_time(dt_str):
    try:
        dt = datetime.fromisoformat(str(dt_str).replace("Z", ""))
        return dt.strftime("%H:%M")
    except Exception:
        return str(dt_str)


def parse_price(price_str):
    try:
        if isinstance(price_str, (int, float)):
            return price_str
        s = str(price_str).replace("$", "").replace(",", "").replace("US", "").strip()
        return float(s) if s else 0
    except Exception:
        return 0


@st.cache_data(ttl=600)
def search_fli(origin, dest, depart_date_str, adults, cabin_code, stops_code):
    try:
        filters = FlightSearchFilters(
            passenger_info=PassengerInfo(adults=adults),
            flight_segments=[
                FlightSegment(
                    departure_airport=[[getattr(Airport, origin), 0]],
                    arrival_airport=[[getattr(Airport, dest), 0]],
                    travel_date=depart_date_str,
                )
            ],
            seat_type=getattr(SeatType, cabin_code),
            stops=getattr(MaxStops, stops_code),
            sort_by=SortBy.CHEAPEST,
        )
        results = SearchFlights().search(filters) or []
        data = []
        for f in results:
            legs = f.legs if hasattr(f, "legs") else []
            first = legs[0] if legs else None
            last = legs[-1] if legs else None
            data.append({
                "航空公司": getattr(first, "airline", "N/A") if first else "N/A",
                "航班": getattr(first, "flight_number", "N/A") if first else "N/A",
                "起飛": format_time(getattr(first, "departure_datetime", "")) if first else "N/A",
                "降落": format_time(getattr(last, "arrival_datetime", "")) if last else "N/A",
                "飛行時間": format_duration(int(f.duration)) if hasattr(f, "duration") else "N/A",
                "轉機": f.stops if hasattr(f, "stops") else 0,
                "票價": f.price if hasattr(f, "price") else 0,
                "幣別": "USD",
            })
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"fli 查詢錯誤：{str(e)}")
        return pd.DataFrame()


@st.cache_data(ttl=600)
def search_fast(origin, dest, depart_date_str, adults, seat_type, trip_type):
    try:
        result = get_flights(
            flight_data=[FlightData(date=depart_date_str, from_airport=origin, to_airport=dest)],
            trip=trip_type,
            seat=seat_type,
            passengers=Passengers(adults=adults),
            fetch_mode="fallback",
        )
        data = []
        for f in result.flights:
            data.append({
                "航空公司": getattr(f, "name", "N/A"),
                "航班": "N/A",
                "起飛": getattr(f, "departure", "N/A"),
                "降落": getattr(f, "arrival", "N/A"),
                "飛行時間": getattr(f, "duration", "N/A"),
                "轉機": getattr(f, "stops", 0),
                "票價": parse_price(getattr(f, "price", "0")),
                "幣別": "USD",
            })
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"fast-flights 查詢錯誤：{str(e)}")
        return pd.DataFrame()


@st.cache_data(ttl=600)
def search_serpapi(origin, dest, depart_date_str, adults, api_key, currency="USD"):
    try:
        params = {
            "engine": "google_flights",
            "departure_id": origin,
            "arrival_id": dest,
            "outbound_date": depart_date_str,
            "currency": currency,
            "type": "2",
            "adults": adults,
            "api_key": api_key,
        }
        search = GoogleSearch(params)
        results = search.get_dict()
        flights_list = results.get("best_flights", []) + results.get("other_flights", [])
        data = []
        for f in flights_list:
            legs = f.get("flights", [])
            if not legs:
                continue
            first = legs[0]
            last = legs[-1]
            dep_time = str(first.get("departure_airport", {}).get("time", "N/A"))
            arr_time = str(last.get("arrival_airport", {}).get("time", "N/A"))
            data.append({
                "航空公司": first.get("airline", "N/A"),
                "航班": f"{first.get('airline_code', '')}{first.get('flight_number', '')}",
                "起飛": dep_time.split(" ")[-1] if " " in dep_time else dep_time,
                "降落": arr_time.split(" ")[-1] if " " in arr_time else arr_time,
                "飛行時間": format_duration(f.get("total_duration", 0)),
                "轉機": len(legs) - 1,
                "票價": f.get("price", 0),
                "幣別": currency,
            })
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"SerpApi 查詢錯誤：{str(e)}")
        return pd.DataFrame()


st.title("✈️ 機票查詢系統 - 三合一比較版")
st.markdown("整合 **3 大資料來源**，比較不同 API 的查詢結果")
st.divider()

with st.sidebar:
    st.header("搜尋條件")
    source_options = []
    if FLI_OK:
        source_options.append("[1] fli (免費)")
    if FAST_OK:
        source_options.append("[2] fast-flights (免費)")
    if SERP_OK:
        source_options.append("[3] SerpApi (需金鑰)")
    if len(source_options) > 1:
        source_options.append("[All] 全部來源（比較模式）")

    if not source_options:
        st.error("沒有可用的 API")
        st.stop()

    data_source = st.selectbox("資料來源", source_options)
    st.divider()

    origin_label = st.selectbox("出發地", list(AIRPORTS.keys()), index=0)
    dest_label = st.selectbox("目的地", list(AIRPORTS.keys()), index=3)

    depart_date = st.date_input(
        "出發日期",
        value=date.today() + timedelta(days=14),
        min_value=date.today(),
        max_value=date.today() + timedelta(days=330),
    )

    adults = st.number_input("成人人數", min_value=1, max_value=9, value=1)
    cabin = st.selectbox("舱等", ["經濟", "豪華經濟", "商務", "頭等"])
    stops = st.selectbox("轉機次數", ["全部", "直飛", "1 次轉機"])

    if ("SerpApi" in data_source) or ("全部" in data_source):
        st.divider()
        try:
            default_key = st.secrets.get("SERPAPI_KEY", "")
        except Exception:
            default_key = ""
        serp_key = st.text_input("SerpApi 金鑰", type="password", value=default_key)
    else:
        serp_key = ""

    st.divider()
    search_btn = st.button("搜尋航班", type="primary", use_container_width=True)
    st.caption(f"可用 API：{sum([FLI_OK, FAST_OK, SERP_OK])} / 3")


def show_results(df, source_name):
    if df.empty:
        st.warning(f"{source_name} 查無資料")
        return
    st.subheader(f"{source_name} - 共 {len(df)} 筆")
    col1, col2, col3 = st.columns(3)
    col1.metric("最低", f"{df['票價'].min():,.0f}")
    col2.metric("最高", f"{df['票價'].max():,.0f}")
    col3.metric("平均", f"{df['票價'].mean():,.0f}")

    for idx, row in df.head(10).iterrows():
        total = row["票價"] * adults
        with st.container(border=True):
            c1, c2, c3, c4, c5 = st.columns([1.8, 1.5, 1.5, 1.5, 1.7])
            with c1:
                st.markdown(f"**{row['航空公司']}**")
                st.caption(f"{row['航班']}")
            with c2:
                st.markdown(f"**{row['起飛']}**")
            with c3:
                st.markdown(f"**{row['降落']}**")
            with c4:
                st.markdown(f"{row['飛行時間']}")
                stops_text = "直飛" if row["轉機"] == 0 else f"轉 {row['轉機']}"
                st.caption(stops_text)
            with c5:
                st.markdown(f"### {row['幣別']} {total:,.0f}")
                st.caption(f"{adults} 位")

    csv = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        f"下載 {source_name} 結果",
        data=csv,
        file_name=f"{source_name}_{depart_date}.csv",
        mime="text/csv",
        key=f"dl_{source_name}",
    )


if search_btn:
    origin_code = AIRPORTS[origin_label]
    dest_code = AIRPORTS[dest_label]

    if origin_code == dest_code:
        st.warning("出發地與目的地不能相同")
        st.stop()

    date_str = depart_date.strftime("%Y-%m-%d")
    cabin_map_fli = {
        "經濟": "ECONOMY",
        "豪華經濟": "PREMIUM_ECONOMY",
        "商務": "BUSINESS",
        "頭等": "FIRST",
    }
    stops_map_fli = {
        "全部": "ANY",
        "直飛": "NON_STOP",
        "1 次轉機": "ONE_STOP",
    }
    seat_map_fast = {
        "經濟": "economy",
        "豪華經濟": "premium-economy",
        "商務": "business",
        "頭等": "first",
    }

    if "全部" in data_source:
        all_tabs = st.tabs(["fli", "fast-flights", "SerpApi"])
        tab_fli, tab_fast, tab_serp = all_tabs

        with tab_fli:
            if FLI_OK:
                with st.spinner("fli 搜尋中..."):
                    df = search_fli(
                        origin_code, dest_code, date_str, adults,
                        cabin_map_fli[cabin], stops_map_fli[stops]
                    )
                show_results(df, "fli")
            else:
                st.error("fli 未安裝")

        with tab_fast:
            if FAST_OK:
                with st.spinner("fast-flights 搜尋中..."):
                    df = search_fast(
                        origin_code, dest_code, date_str, adults,
                        seat_map_fast[cabin], "one-way"
                    )
                show_results(df, "fast-flights")
            else:
                st.error("fast-flights 未安裝")

        with tab_serp:
            if SERP_OK and serp_key:
                with st.spinner("SerpApi 搜尋中..."):
                    df = search_serpapi(
                        origin_code, dest_code, date_str, adults, serp_key
                    )
                show_results(df, "SerpApi")
            elif not serp_key:
                st.warning("請先輸入 SerpApi 金鑰")
            else:
                st.error("SerpApi 未安裝")

    elif "fli" in data_source:
        with st.spinner("fli 搜尋中..."):
            df = search_fli(
                origin_code, dest_code, date_str, adults,
                cabin_map_fli[cabin], stops_map_fli[stops]
            )
        show_results(df, "fli")

    elif "fast-flights" in data_source:
        with st.spinner("fast-flights 搜尋中..."):
            df = search_fast(
                origin_code, dest_code, date_str, adults,
                seat_map_fast[cabin], "one-way"
            )
        show_results(df, "fast-flights")

    elif "SerpApi" in data_source:
        if not serp_key:
            st.warning("請先輸入 SerpApi 金鑰")
        else:
            with st.spinner("SerpApi 搜尋中..."):
                df = search_serpapi(
                    origin_code, dest_code, date_str, adults, serp_key
                )
            show_results(df, "SerpApi")

else:
    st.info("請在左側選擇搜尋條件與資料來源，然後點擊「搜尋航班」")

    with st.expander("三個 API 比較", expanded=True):
        st.markdown("""
        | 來源 | 費用 | 優點 | 缺點 |
        |------|------|------|------|
        | **fli** | 免費 | Google Flights 直連、快速、穩定 | 偶爾被 Google 擋 |
        | **fast-flights** | 免費 | 強型別、繁中支援 | 速度較慢 |
        | **SerpApi** | 250 次/月免費 | 最穩定、資料最完整 | 需註冊金鑰 |
        """)

    st.subheader("API 狀態檢查")
    c1, c2, c3 = st.columns(3)
    c1.metric("fli", "可用" if FLI_OK else "未安裝")
    c2.metric("fast-flights", "可用" if FAST_OK else "未安裝")
    c3.metric("SerpApi", "可用" if SERP_OK else "未安裝")
