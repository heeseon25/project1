import os
import sqlite3

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# =============================
# 기본 설정
# =============================
st.set_page_config(
    page_title="노후 재무 시뮬레이터",
    page_icon="🌿",
    layout="wide"
)

DB_PATH = "plco.db"
CURRENT_YEAR = 2026
MAX_AGE = 100


# =============================
# 디자인
# =============================
st.markdown(
    """
    <style>
    .main {
        background-color: #faf9f7;
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
    }
    .title-box {
        background: linear-gradient(135deg, #f7efe5 0%, #eef3f7 100%);
        padding: 34px 38px;
        border-radius: 24px;
        margin-bottom: 28px;
        border: 1px solid #eee4d8;
    }
    .title-box h1 {
        margin: 0;
        color: #2f3542;
        font-size: 2.2rem;
        font-weight: 800;
    }
    .title-box p {
        margin-top: 12px;
        color: #5f6673;
        font-size: 1.03rem;
        line-height: 1.7;
    }
    .metric-card {
        background: white;
        padding: 22px 24px;
        border-radius: 20px;
        border: 1px solid #ede7df;
        box-shadow: 0 6px 20px rgba(60, 50, 40, 0.06);
        min-height: 128px;
    }
    .metric-label {
        color: #7a7f89;
        font-size: 0.92rem;
        margin-bottom: 10px;
    }
    .metric-value {
        color: #2f3542;
        font-size: 1.55rem;
        font-weight: 800;
    }
    .metric-sub {
        color: #8b9099;
        font-size: 0.85rem;
        margin-top: 8px;
    }
    .insight-box {
        background: white;
        padding: 26px 28px;
        border-radius: 22px;
        border: 1px solid #ede7df;
        box-shadow: 0 6px 20px rgba(60, 50, 40, 0.06);
        line-height: 1.8;
        color: #3c414a;
        font-size: 1.02rem;
    }
    .good { color: #2e7d32; font-weight: 800; }
    .warn { color: #b7791f; font-weight: 800; }
    .bad { color: #c0392b; font-weight: 800; }
    .small-note {
        color: #868b95;
        font-size: 0.86rem;
        line-height: 1.6;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# =============================
# DB 함수
# =============================
def check_db_exists():
    if not os.path.exists(DB_PATH):
        st.error("plco.db 파일을 찾을 수 없습니다. app.py와 같은 폴더에 plco.db를 넣어주세요.")
        st.stop()


@st.cache_data
def load_data(query, params=None):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


# =============================
# 계산 함수
# =============================
def won(value):
    if pd.isna(value):
        return "-"
    value = float(value)
    if abs(value) >= 100000000:
        return f"{value / 100000000:,.1f}억 원"
    return f"{value:,.0f}원"


def get_nearest_pension(monthly_income, contribution_years):
    query = """
    SELECT monthly_income_won, contribution_years, expected_pension_won
    FROM official_pension
    ORDER BY
        ABS(monthly_income_won - ?) + ABS(contribution_years - ?) * 100000
    LIMIT 1;
    """
    return load_data(query, (monthly_income, contribution_years)).iloc[0]


def get_cpi(year):
    query = """
    SELECT year, cpi
    FROM cpi
    ORDER BY ABS(year - ?)
    LIMIT 1;
    """
    row = load_data(query, (year,)).iloc[0]
    return int(row["year"]), float(row["cpi"])


def get_rate_range(start_year, end_year):
    query = """
    SELECT year, base_rate
    FROM ratefull
    WHERE year BETWEEN ? AND ?
    ORDER BY year;
    """
    return load_data(query, (start_year, end_year))


def simulate_until_100(
    current_age,
    retire_age,
    monthly_income,
    current_asset,
    monthly_saving,
    current_monthly_living_cost,
    contribution_years,
):
    retire_year = CURRENT_YEAR + (retire_age - current_age)

    pension_row = get_nearest_pension(monthly_income, contribution_years)
    monthly_pension = float(pension_row["expected_pension_won"])

    current_cpi_year, current_cpi = get_cpi(CURRENT_YEAR)
    retire_cpi_year, retire_cpi = get_cpi(retire_year)

    # 은퇴 전: 매년 기준금리로 자산 성장 + 저축 누적
    asset = float(current_asset)
    pre_rates = get_rate_range(CURRENT_YEAR, retire_year)

    for _, row in pre_rates.iterrows():
        rate = float(row["base_rate"]) / 100
        asset = asset * (1 + rate) + monthly_saving * 12

    asset_at_retirement = asset

    # 은퇴 시점 생활비: 현재 생활비를 CPI 비율로 보정
    monthly_living_cost = current_monthly_living_cost * (retire_cpi / current_cpi)

    # 은퇴 후: 매년 CPI 변화 반영 + 연금 수령 + 생활비 지출 + 잔여자산 기준금리 성장
    rows = []
    depletion_age = MAX_AGE
    previous_cpi_year, previous_cpi = retire_cpi_year, retire_cpi

    for age in range(retire_age, MAX_AGE + 1):
        year = CURRENT_YEAR + (age - current_age)
        _, year_cpi = get_cpi(year)

        if age > retire_age:
            monthly_living_cost *= year_cpi / previous_cpi

        _, base_rate = get_rate_for_year(year)
        annual_pension = monthly_pension * 12
        annual_living_cost = monthly_living_cost * 12
        annual_gap = annual_living_cost - annual_pension

        start_asset = asset
        asset = asset + annual_pension - annual_living_cost
        asset = asset * (1 + base_rate / 100)

        rows.append({
            "age": age,
            "year": year,
            "start_asset": start_asset,
            "end_asset": asset,
            "monthly_living_cost": monthly_living_cost,
            "monthly_pension": monthly_pension,
            "annual_gap": annual_gap,
            "cpi": year_cpi,
            "base_rate": base_rate,
        })

        previous_cpi = year_cpi

        if asset <= 0 and depletion_age == MAX_AGE:
            depletion_age = age
            # 이후 그래프가 너무 깨지지 않도록 0으로 고정
            asset = 0

    sim_df = pd.DataFrame(rows)

    total_needed_gap = sim_df["annual_gap"].clip(lower=0).sum()
    readiness = 100 if total_needed_gap <= 0 else min(100, asset_at_retirement / total_needed_gap * 100)
    pension_coverage = min(100, monthly_pension / monthly_living_cost * 100)

    return {
        "retire_year": retire_year,
        "asset_at_retirement": asset_at_retirement,
        "monthly_pension": monthly_pension,
        "future_monthly_living_cost": sim_df.loc[sim_df["age"] == retire_age, "monthly_living_cost"].iloc[0],
        "depletion_age": depletion_age,
        "readiness": readiness,
        "pension_coverage": pension_coverage,
        "matched_income": int(pension_row["monthly_income_won"]),
        "matched_years": int(pension_row["contribution_years"]),
        "sim_df": sim_df,
    }


def get_rate_for_year(year):
    query = """
    SELECT year, base_rate
    FROM ratefull
    ORDER BY ABS(year - ?)
    LIMIT 1;
    """
    row = load_data(query, (year,)).iloc[0]
    return int(row["year"]), float(row["base_rate"])


def make_insight(result, current_monthly_living_cost, retire_age):
    readiness = result["readiness"]
    pension_coverage = result["pension_coverage"]
    depletion_age = result["depletion_age"]
    future_cost = result["future_monthly_living_cost"]

    if readiness >= 85 and depletion_age >= 100:
        label = "안정"
        cls = "good"
        text = f"""
        <span class='{cls}'>현재 노후 준비 수준은 안정 단계에 가깝습니다.</span><br><br>
        현재 월 생활비 {won(current_monthly_living_cost)}는 은퇴 시점에 약 <b>{won(future_cost)}</b> 수준으로 증가할 수 있습니다.
        예상 국민연금은 은퇴 시점 생활비의 약 <b>{pension_coverage:.1f}%</b>를 충당합니다.<br><br>
        은퇴 후에도 매년 CPI를 반영해 생활비를 증가시켜 계산했을 때, 현재 자산과 저축 흐름은 100세까지 비교적 안정적으로 유지될 가능성이 있습니다.
        다만 장기 예측은 불확실성이 크기 때문에 저축 습관과 위험 관리가 계속 필요합니다.
        """
    elif readiness >= 60:
        label = "주의"
        cls = "warn"
        text = f"""
        <span class='{cls}'>현재 노후 준비 수준은 주의 단계입니다.</span><br><br>
        현재 월 생활비 {won(current_monthly_living_cost)}는 은퇴 시점에 약 <b>{won(future_cost)}</b>까지 증가할 수 있습니다.
        예상 국민연금은 필요한 생활비의 약 <b>{pension_coverage:.1f}%</b>를 충당합니다.<br><br>
        이번 계산은 은퇴 이후에도 매년 물가 상승을 반영했습니다. 그 결과 자산은 <b>{depletion_age}세 전후</b>까지 유지될 가능성이 있습니다.
        100세까지 안정적으로 생활하려면 월 저축액을 늘리거나, 자산 성장 전략을 함께 고민할 필요가 있습니다.
        """
    else:
        label = "위험"
        cls = "bad"
        text = f"""
        <span class='{cls}'>현재 노후 준비 수준은 위험 단계에 가깝습니다.</span><br><br>
        은퇴 이후에도 생활비가 CPI에 따라 계속 상승한다고 가정하면, 현재 자산 흐름은 장기 노후 생활을 충분히 감당하기 어려울 수 있습니다.
        예상 국민연금은 은퇴 시점 생활비의 약 <b>{pension_coverage:.1f}%</b>만 충당합니다.<br><br>
        특히 문제는 단순히 연금이 적다는 점이 아니라, <b>물가 상승 속도에 비해 자산이 충분히 빠르게 늘지 않는 구조</b>입니다.
        월 저축액을 늘리거나 은퇴 시점을 조정하는 등 현실적인 재무 전략이 필요합니다.
        """

    return label, cls, text


# =============================
# 화면 구성
# =============================
check_db_exists()

st.markdown(
    """
    <div class="title-box">
        <h1>100세 시대 노후 재무 시뮬레이터</h1>
        <p>
            국민연금, 소비자물가지수(CPI), 기준금리 데이터를 활용해
            현재의 소득·자산·저축 수준이 미래 노후 생활을 감당할 수 있는지 분석합니다.
            단순 계산이 아니라, 물가 상승과 자산 성장 속도를 함께 비교하는 재무 의사결정 지원 대시보드입니다.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

# 상단 데이터 차트
st.subheader("데이터 기반 장기 전망")
col_a, col_b = st.columns(2)

with col_a:
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
        title="대한민국 CPI 실제값 및 예측값",
        markers=True,
    )
    fig_cpi.update_layout(height=360, template="plotly_white")
    st.plotly_chart(fig_cpi, use_container_width=True)
    with st.expander("사용된 SQL과 인사이트 보기"):
        st.code(sql_cpi, language="sql")
        st.info("CPI가 상승할수록 같은 생활 수준을 유지하기 위해 필요한 생활비도 증가합니다. 이 데이터는 은퇴 시점과 은퇴 이후의 생활비를 매년 보정하는 데 사용됩니다.")

with col_b:
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
        title="대한민국 기준금리 실제값 및 예측값",
        markers=True,
    )
    fig_rate.update_layout(height=360, template="plotly_white")
    st.plotly_chart(fig_rate, use_container_width=True)
    with st.expander("사용된 SQL과 인사이트 보기"):
        st.code(sql_rate, language="sql")
        st.info("기준금리는 자산 성장의 보수적인 기준선으로 활용됩니다. 투자수익률 대신 기준금리를 사용해 개인별 투자 성과 차이를 줄이고 객관적인 시뮬레이션 기준을 만들었습니다.")

st.divider()

# 입력 영역
st.subheader("내 노후 재무 시뮬레이션")
left, right = st.columns(2)

with left:
    current_age = st.number_input("현재 나이", min_value=1, max_value=99, value=22, step=1)
    retire_age = st.number_input("은퇴 희망 나이", min_value=40, max_value=80, value=65, step=1)
    monthly_income = st.number_input("월 소득(원)", min_value=0, value=1000000, step=100000)
    current_asset = st.number_input("현재 자산(원)", min_value=0, value=7800000, step=100000)

with right:
    monthly_saving = st.number_input("월 저축액(원)", min_value=0, value=400000, step=100000)
    current_monthly_living_cost = st.number_input("현재 월 생활비(원)", min_value=0, value=600000, step=100000)
    contribution_years = st.number_input("국민연금 예상 가입기간(년)", min_value=10, max_value=40, value=30, step=5)

if retire_age <= current_age:
    st.warning("은퇴 희망 나이는 현재 나이보다 커야 합니다.")
    st.stop()

if st.button("분석하기", use_container_width=True):
    result = simulate_until_100(
        current_age=current_age,
        retire_age=retire_age,
        monthly_income=monthly_income,
        current_asset=current_asset,
        monthly_saving=monthly_saving,
        current_monthly_living_cost=current_monthly_living_cost,
        contribution_years=contribution_years,
    )

    label, cls, insight_html = make_insight(result, current_monthly_living_cost, retire_age)

    st.markdown("### 분석 결과")
    m1, m2, m3, m4 = st.columns(4)

    with m1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">은퇴 시점 예상 자산</div>
            <div class="metric-value">{won(result['asset_at_retirement'])}</div>
            <div class="metric-sub">기준금리 기반 복리 + 저축 반영</div>
        </div>
        """, unsafe_allow_html=True)

    with m2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">예상 국민연금</div>
            <div class="metric-value">월 {won(result['monthly_pension'])}</div>
            <div class="metric-sub">공식 예상연금월액표 기준</div>
        </div>
        """, unsafe_allow_html=True)

    with m3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">은퇴 시점 월 생활비</div>
            <div class="metric-value">월 {won(result['future_monthly_living_cost'])}</div>
            <div class="metric-sub">CPI로 현재 생활비 보정</div>
        </div>
        """, unsafe_allow_html=True)

    with m4:
        depletion = "100세 이상" if result["depletion_age"] >= 100 else f"{result['depletion_age']}세"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">자산 소진 예상 나이</div>
            <div class="metric-value">{depletion}</div>
            <div class="metric-sub">은퇴 후 매년 CPI 반영</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    sim_df = result["sim_df"].copy()

    fig_asset = go.Figure()
    fig_asset.add_trace(go.Scatter(
        x=sim_df["age"],
        y=sim_df["end_asset"],
        mode="lines+markers",
        name="예상 자산",
    ))
    fig_asset.add_trace(go.Scatter(
        x=sim_df["age"],
        y=sim_df["monthly_living_cost"] * 12,
        mode="lines+markers",
        name="연간 생활비",
    ))
    fig_asset.update_layout(
        title="은퇴 이후 자산 흐름과 생활비 변화",
        xaxis_title="나이",
        yaxis_title="금액(원)",
        template="plotly_white",
        height=430,
    )
    st.plotly_chart(fig_asset, use_container_width=True)

    st.markdown("### 데이터 기반 인사이트")
    st.markdown(
        f"""
        <div class="insight-box">
            <p><b>노후 준비 상태:</b> <span class="{cls}">{label}</span></p>
            {insight_html}
            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
            <p class="small-note">
                국민연금 조회 시 입력 소득과 가입기간에 가장 가까운 공식 표 값을 사용했습니다.<br>
                매칭된 기준소득월액: {won(result['matched_income'])}, 매칭된 가입기간: {result['matched_years']}년
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("시뮬레이션에 사용된 주요 SQL 보기"):
        st.code(
            """
SELECT monthly_income_won, contribution_years, expected_pension_won
FROM official_pension
ORDER BY
    ABS(monthly_income_won - ?) + ABS(contribution_years - ?) * 100000
LIMIT 1;
            """,
            language="sql",
        )
        st.code(
            """
SELECT year, cpi
FROM cpi
ORDER BY ABS(year - ?)
LIMIT 1;
            """,
            language="sql",
        )
        st.code(
            """
SELECT year, base_rate
FROM ratefull
ORDER BY ABS(year - ?)
LIMIT 1;
            """,
            language="sql",
        )

    with st.expander("은퇴 후 연도별 시뮬레이션 표 보기"):
        st.dataframe(
            sim_df[[
                "age", "year", "end_asset", "monthly_living_cost",
                "monthly_pension", "annual_gap", "cpi", "base_rate"
            ]],
            use_container_width=True,
        )
