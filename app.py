import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="플코 노후 재무 시뮬레이터", layout="wide")

st.title("🌱 플코: 100세 시대 노후 재무 시뮬레이터")
st.write("물가, 기준금리, 국민연금 데이터를 활용해 노후 재정 상태를 분석합니다.")

db_path = "plco.db"

if not os.path.exists(db_path):
    st.error("plco.db 파일을 찾을 수 없어요. app.py와 같은 폴더에 넣어주세요.")
    st.stop()

def load_data(query, params=None):
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

# -----------------------------
# 1. CPI 그래프
# -----------------------------
st.header("📈 1. 대한민국 CPI 장기 예측")

sql_cpi = """
SELECT year, cpi, data_type
FROM cpi
ORDER BY year;
"""

df_cpi = load_data(sql_cpi)

fig_cpi = px.line(
    df_cpi,
    x="year",
    y="cpi",
    color="data_type",
    title="대한민국 소비자물가지수(CPI) 실제값 및 예측값"
)

st.plotly_chart(fig_cpi, use_container_width=True)

st.write("**사용된 SQL**")
st.code(sql_cpi, language="sql")

st.info("""
💡 **인사이트**
- CPI가 장기적으로 상승하면 같은 생활 수준을 유지하기 위해 필요한 생활비도 증가합니다.
- 플코는 이 데이터를 활용해 은퇴 시점의 미래 생활비를 계산합니다.
""")

# -----------------------------
# 2. 기준금리 그래프
# -----------------------------
st.header("💰 2. 기준금리 장기 예측")

sql_rate = """
SELECT year, base_rate, data_type
FROM ratefull
ORDER BY year;
"""

df_rate = load_data(sql_rate)

fig_rate = px.line(
    df_rate,
    x="year",
    y="base_rate",
    color="data_type",
    title="대한민국 기준금리 실제값 및 예측값"
)

st.plotly_chart(fig_rate, use_container_width=True)

st.write("**사용된 SQL**")
st.code(sql_rate, language="sql")

st.info("""
💡 **인사이트**
- 기준금리는 자산이 얼마나 성장할 수 있는지 판단하는 최소 기준선으로 활용됩니다.
- 물가 상승률보다 자산 성장률이 낮으면 실질 구매력이 줄어들 수 있습니다.
""")

# -----------------------------
# 3. 사용자 입력 기반 시뮬레이션
# -----------------------------
st.header("🧓 3. 내 노후 재무 시뮬레이션")

col1, col2 = st.columns(2)

with col1:
    age = st.number_input("현재 나이", min_value=1, max_value=100, value=22)
    retire_age = st.number_input("은퇴 희망 나이", min_value=40, max_value=80, value=65)
    income = st.number_input("월 소득(원)", min_value=0, value=3000000, step=100000)
    asset = st.number_input("현재 자산(원)", min_value=0, value=10000000, step=1000000)

with col2:
    monthly_saving = st.number_input("월 저축액(원)", min_value=0, value=500000, step=100000)
    monthly_living_cost = st.number_input("현재 월 생활비(원)", min_value=0, value=1500000, step=100000)
    pension_years = st.number_input("국민연금 예상 가입기간(년)", min_value=10, max_value=40, value=30, step=5)

current_year = 2026
retire_year = current_year + (retire_age - age)

if st.button("분석하기"):
    # 국민연금: 가장 가까운 소득/가입기간 기준 조회
    sql_pension = """
    SELECT monthly_income_won, contribution_years, expected_pension_won
    FROM official_pension
    ORDER BY 
        ABS(monthly_income_won - ?) + ABS(contribution_years - ?) * 100000
    LIMIT 1;
    """

    pension_df = load_data(sql_pension, (income, pension_years))
    expected_pension = pension_df.iloc[0]["expected_pension_won"]

    # 현재 CPI, 은퇴연도 CPI
    current_cpi = load_data(
        "SELECT cpi FROM cpi WHERE year = ?;",
        (current_year,)
    ).iloc[0]["cpi"]

    retire_cpi = load_data(
        "SELECT cpi FROM cpi WHERE year = ?;",
        (retire_year,)
    ).iloc[0]["cpi"]

    future_living_cost = monthly_living_cost * (retire_cpi / current_cpi)

    # 기준금리 기반 자산 성장
    rate_df = load_data(
        """
        SELECT year, base_rate
        FROM ratefull
        WHERE year BETWEEN ? AND ?
        ORDER BY year;
        """,
        (current_year, retire_year)
    )

    future_asset = asset
    for _, row in rate_df.iterrows():
        future_asset = future_asset * (1 + row["base_rate"] / 100) + monthly_saving * 12

    monthly_gap = future_living_cost - expected_pension

    if monthly_gap <= 0:
        depletion_age = 100
        readiness = 100
    else:
        months_can_cover = future_asset / monthly_gap
        depletion_age = min(100, int(retire_age + months_can_cover / 12))
        needed_until_100 = monthly_gap * 12 * (100 - retire_age)
        readiness = min(100, future_asset / needed_until_100 * 100)

    pension_coverage = min(100, expected_pension / future_living_cost * 100)

    st.subheader("📊 분석 결과")

    m1, m2, m3, m4 = st.columns(4)

    m1.metric("은퇴 시점 예상 자산", f"{future_asset:,.0f}원")
    m2.metric("예상 국민연금", f"월 {expected_pension:,.0f}원")
    m3.metric("은퇴 시점 월 생활비", f"월 {future_living_cost:,.0f}원")
    m4.metric("자산 소진 예상 나이", f"{depletion_age}세")

    # 자산 vs 필요 생활비 비교용 데이터
    sim_df = pd.DataFrame({
        "항목": ["은퇴 시점 예상 자산", "100세까지 필요한 부족분"],
        "금액": [
            future_asset,
            max(monthly_gap, 0) * 12 * (100 - retire_age)
        ]
    })

    fig_sim = px.bar(
        sim_df,
        x="항목",
        y="금액",
        title="은퇴 자산과 100세까지 필요한 자금 비교"
    )

    st.plotly_chart(fig_sim, use_container_width=True)

    st.write("**사용된 SQL - 국민연금 조회**")
    st.code(sql_pension, language="sql")

    st.info(f"""
    💡 **플코 인사이트**

    현재 월 생활비 {monthly_living_cost:,.0f}원은 은퇴 시점에 약 **{future_living_cost:,.0f}원** 수준으로 증가할 수 있습니다.

    예상 국민연금은 은퇴 후 필요 생활비의 약 **{pension_coverage:.1f}%**를 충당합니다.

    현재 저축과 기준금리 기반 자산 성장을 고려하면 자산은 약 **{depletion_age}세 전후**까지 유지될 가능성이 있습니다.

    100세까지 안정적으로 생활하려면 저축액을 늘리거나, 장기적인 자산 성장 전략을 함께 고민할 필요가 있습니다.
    """)
