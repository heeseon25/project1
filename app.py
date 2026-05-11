import os
import sqlite3
import textwrap

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# =============================
# 기본 설정
# =============================
st.set_page_config(
    page_title="100세 시대 노후 재무 시뮬레이터",
    page_icon="🌱",
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
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;600;700;800&display=swap');

    html, body, [class*="css"]  {
        font-family: 'Noto Sans KR', sans-serif;
    }
    .stApp {
        background: linear-gradient(180deg, #fbfaf7 0%, #f5f7fb 100%);
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1280px;
    }
    .hero {
        background: linear-gradient(135deg, #eaf7ef 0%, #f6efe7 52%, #eef4ff 100%);
        padding: 38px 42px;
        border-radius: 30px;
        margin-bottom: 30px;
        border: 1px solid rgba(190, 200, 190, 0.45);
        box-shadow: 0 14px 36px rgba(61, 72, 85, 0.08);
    }
    .hero h1 {
        margin: 0;
        color: #263238;
        font-size: 2.35rem;
        font-weight: 800;
        letter-spacing: -0.04em;
    }
    .hero .subtitle {
        margin-top: 12px;
        color: #52606d;
        font-size: 1.05rem;
        line-height: 1.8;
    }
    .tag-row {
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
        margin-top: 20px;
    }
    .tag {
        background: rgba(255,255,255,0.75);
        border: 1px solid rgba(190, 200, 190, 0.5);
        border-radius: 999px;
        padding: 8px 14px;
        color: #4b5563;
        font-size: 0.9rem;
        font-weight: 700;
    }
    .section-card {
        background: rgba(255, 255, 255, 0.92);
        border-radius: 26px;
        border: 1px solid #ece7df;
        box-shadow: 0 10px 30px rgba(60, 50, 40, 0.06);
        padding: 26px;
        margin-bottom: 24px;
    }
    .metric-card {
        background: white;
        padding: 22px 24px;
        border-radius: 22px;
        border: 1px solid #ebe7df;
        box-shadow: 0 8px 22px rgba(60, 50, 40, 0.06);
        min-height: 140px;
    }
    .metric-label {
        color: #7a7f89;
        font-size: 0.9rem;
        margin-bottom: 10px;
        font-weight: 700;
    }
    .metric-value {
        color: #263238;
        font-size: 1.55rem;
        font-weight: 800;
        letter-spacing: -0.03em;
    }
    .metric-sub {
        color: #8b9099;
        font-size: 0.84rem;
        margin-top: 8px;
        line-height: 1.5;
    }
    .score-box {
        background: white;
        padding: 26px 28px;
        border-radius: 26px;
        border: 1px solid #ebe7df;
        box-shadow: 0 10px 28px rgba(60, 50, 40, 0.07);
        margin-bottom: 22px;
    }
    .score-title {
        color: #6b7280;
        font-size: 0.95rem;
        font-weight: 800;
        margin-bottom: 8px;
    }
    .score-value {
        font-size: 2.8rem;
        font-weight: 900;
        letter-spacing: -0.06em;
        color: #263238;
        margin-bottom: 4px;
    }
    .status-pill {
        display: inline-block;
        padding: 9px 15px;
        border-radius: 999px;
        font-weight: 800;
        margin-top: 10px;
        font-size: 0.98rem;
    }
    .status-good {
        background: #dcfce7;
        color: #166534;
    }
    .status-warn {
        background: #fef3c7;
        color: #92400e;
    }
    .status-bad {
        background: #fee2e2;
        color: #991b1b;
    }
    .insight-box {
        background: white;
        padding: 28px 30px;
        border-radius: 26px;
        border: 1px solid #ebe7df;
        box-shadow: 0 10px 28px rgba(60, 50, 40, 0.07);
        line-height: 1.85;
        color: #3c414a;
        font-size: 1.02rem;
    }
    .insight-box h3 {
        margin-top: 0;
        color: #263238;
        font-size: 1.35rem;
    }
    .insight-step {
        background: #fafafa;
        border: 1px solid #eeeeee;
        border-radius: 18px;
        padding: 18px 20px;
        margin: 14px 0;
    }
    .insight-step b {
        color: #263238;
    }
    .good { color: #15803d; font-weight: 900; }
    .warn { color: #b7791f; font-weight: 900; }
    .bad { color: #c0392b; font-weight: 900; }
    .small-note {
        color: #868b95;
        font-size: 0.86rem;
        line-height: 1.7;
    }
    div[data-testid="stMetric"] {
        background: white;
        border: 1px solid #ebe7df;
        border-radius: 18px;
        padding: 15px 16px;
    }
    @media (prefers-color-scheme: dark) {

    .stApp {
        background: #111827 !important;
    }

    .hero,
    .section-card,
    .metric-card,
    .score-box,
    .insight-box,
    .insight-step {
        background: #1f2937 !important;
        border: 1px solid #374151 !important;
        color: #f3f4f6 !important;
    }

    .hero h1,
    .metric-value,
    .insight-box h3,
    .insight-step b {
        color: #f9fafb !important;
    }

    .metric-label,
    .metric-sub,
    .score-title,
    .small-note,
    .hero .subtitle,
    .tag {
        color: #d1d5db !important;
    }

    .tag {
        background: #374151 !important;
        border: 1px solid #4b5563 !important;
    }

    .status-good {
        background: #14532d !important;
        color: #bbf7d0 !important;
    }

    .status-warn {
        background: #78350f !important;
        color: #fde68a !important;
    }

    .status-bad {
        background: #7f1d1d !important;
        color: #fecaca !important;
    }
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
    if abs(value) >= 10000:
        return f"{value / 10000:,.0f}만 원"
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
    """
    DB에 해당 연도가 있으면 그 값을 사용하고,
    2080년 이후처럼 DB 범위를 넘어가면 마지막 두 연도의 증가폭을 이용해 선형 외삽합니다.
    이렇게 해야 100세 시뮬레이션에서 생활비가 2080년 이후 멈추지 않습니다.
    """
    df = load_data("SELECT year, cpi FROM cpi ORDER BY year;")

    exact = df[df["year"] == year]
    if not exact.empty:
        row = exact.iloc[0]
        return int(row["year"]), float(row["cpi"])

    min_year = int(df["year"].min())
    max_year = int(df["year"].max())

    if year > max_year:
        last_two = df.tail(2)
        y1, c1 = int(last_two.iloc[0]["year"]), float(last_two.iloc[0]["cpi"])
        y2, c2 = int(last_two.iloc[1]["year"]), float(last_two.iloc[1]["cpi"])
        slope = (c2 - c1) / (y2 - y1)
        predicted_cpi = c2 + slope * (year - y2)
        return int(year), float(predicted_cpi)

    if year < min_year:
        first_two = df.head(2)
        y1, c1 = int(first_two.iloc[0]["year"]), float(first_two.iloc[0]["cpi"])
        y2, c2 = int(first_two.iloc[1]["year"]), float(first_two.iloc[1]["cpi"])
        slope = (c2 - c1) / (y2 - y1)
        predicted_cpi = c1 - slope * (y1 - year)
        return int(year), float(predicted_cpi)

    row = df.iloc[(df["year"] - year).abs().argsort()[:1]].iloc[0]
    return int(row["year"]), float(row["cpi"])


def get_rate_for_year(year):
    """
    DB에 해당 연도가 있으면 그 값을 사용하고,
    DB 범위를 넘어가면 마지막 두 연도의 추세를 이용해 선형 외삽합니다.
    """
    df = load_data("SELECT year, base_rate FROM ratefull ORDER BY year;")

    exact = df[df["year"] == year]
    if not exact.empty:
        row = exact.iloc[0]
        return int(row["year"]), float(row["base_rate"])

    min_year = int(df["year"].min())
    max_year = int(df["year"].max())

    if year > max_year:
        last_two = df.tail(2)
        y1, r1 = int(last_two.iloc[0]["year"]), float(last_two.iloc[0]["base_rate"])
        y2, r2 = int(last_two.iloc[1]["year"]), float(last_two.iloc[1]["base_rate"])
        slope = (r2 - r1) / (y2 - y1)
        predicted_rate = r2 + slope * (year - y2)
        return int(year), max(0.0, float(predicted_rate))

    if year < min_year:
        first_two = df.head(2)
        y1, r1 = int(first_two.iloc[0]["year"]), float(first_two.iloc[0]["base_rate"])
        y2, r2 = int(first_two.iloc[1]["year"]), float(first_two.iloc[1]["base_rate"])
        slope = (r2 - r1) / (y2 - y1)
        predicted_rate = r1 - slope * (y1 - year)
        return int(year), max(0.0, float(predicted_rate))

    row = df.iloc[(df["year"] - year).abs().argsort()[:1]].iloc[0]
    return int(row["year"]), float(row["base_rate"])


def get_rate_range(start_year, end_year):
    query = """
    SELECT year, base_rate
    FROM ratefull
    WHERE year BETWEEN ? AND ?
    ORDER BY year;
    """
    return load_data(query, (start_year, end_year))


def grow_asset_until_retirement(current_asset, monthly_saving, current_year, retire_year):
    asset = float(current_asset)
    rate_df = get_rate_range(current_year, retire_year)

    for _, row in rate_df.iterrows():
        rate = float(row["base_rate"]) / 100
        asset = asset * (1 + rate) + monthly_saving * 12

    return asset


def calculate_required_growth_rate(current_asset, monthly_saving, years_to_retire, target_asset):
    if target_asset <= 0:
        return 0.0

    low, high = 0.0, 0.25
    for _ in range(70):
        mid = (low + high) / 2
        asset = float(current_asset)
        for _ in range(years_to_retire):
            asset = asset * (1 + mid) + monthly_saving * 12
        if asset < target_asset:
            low = mid
        else:
            high = mid
    return high * 100


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
    years_to_retire = retire_age - current_age

    pension_row = get_nearest_pension(monthly_income, contribution_years)
    monthly_pension = float(pension_row["expected_pension_won"])

    current_cpi_year, current_cpi = get_cpi(CURRENT_YEAR)
    retire_cpi_year, retire_cpi = get_cpi(retire_year)

    asset_at_retirement = grow_asset_until_retirement(
        current_asset, monthly_saving, CURRENT_YEAR, retire_year
    )

    monthly_living_cost = current_monthly_living_cost * (retire_cpi / current_cpi)
    living_cost_multiplier = monthly_living_cost / current_monthly_living_cost if current_monthly_living_cost > 0 else 0

    rows = []
    depletion_age = MAX_AGE
    previous_cpi = retire_cpi
    asset = asset_at_retirement

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
            asset = 0

    sim_df = pd.DataFrame(rows)

    total_needed_gap = sim_df["annual_gap"].clip(lower=0).sum()
    readiness_ratio = 1.0 if total_needed_gap <= 0 else min(1.0, asset_at_retirement / total_needed_gap)
    readiness_score = round(readiness_ratio * 100)

    pension_coverage = min(100, monthly_pension / sim_df.iloc[0]["monthly_living_cost"] * 100)
    years_can_cover_after_retire = max(0, depletion_age - retire_age) if depletion_age < MAX_AGE else MAX_AGE - retire_age
    years_short = max(0, MAX_AGE - depletion_age) if depletion_age < MAX_AGE else 0

    required_growth = calculate_required_growth_rate(
        current_asset=current_asset,
        monthly_saving=monthly_saving,
        years_to_retire=years_to_retire,
        target_asset=total_needed_gap,
    )

    avg_base_rate_until_retire = get_rate_range(CURRENT_YEAR, retire_year)["base_rate"].mean()

    # 맞춤 행동 제안: 저축 20만 원 증가 시 자산 소진 나이 변화
    improved_asset = grow_asset_until_retirement(
        current_asset, monthly_saving + 200000, CURRENT_YEAR, retire_year
    )
    improved_depletion_age = MAX_AGE
    improved_asset_running = improved_asset
    previous_cpi_for_improved = retire_cpi
    improved_monthly_living_cost = current_monthly_living_cost * (retire_cpi / current_cpi)

    for age in range(retire_age, MAX_AGE + 1):
        year = CURRENT_YEAR + (age - current_age)
        _, year_cpi = get_cpi(year)
        if age > retire_age:
            improved_monthly_living_cost *= year_cpi / previous_cpi_for_improved
        _, base_rate = get_rate_for_year(year)
        improved_asset_running = improved_asset_running + monthly_pension * 12 - improved_monthly_living_cost * 12
        improved_asset_running = improved_asset_running * (1 + base_rate / 100)
        previous_cpi_for_improved = year_cpi
        if improved_asset_running <= 0:
            improved_depletion_age = age
            break

    saving_effect_years = max(0, improved_depletion_age - depletion_age) if depletion_age < MAX_AGE else 0

    return {
        "retire_year": retire_year,
        "asset_at_retirement": asset_at_retirement,
        "monthly_pension": monthly_pension,
        "future_monthly_living_cost": sim_df.iloc[0]["monthly_living_cost"],
        "final_monthly_living_cost": sim_df.iloc[-1]["monthly_living_cost"],
        "living_cost_multiplier": living_cost_multiplier,
        "depletion_age": depletion_age,
        "years_can_cover_after_retire": years_can_cover_after_retire,
        "years_short": years_short,
        "readiness_score": readiness_score,
        "pension_coverage": pension_coverage,
        "required_growth": required_growth,
        "avg_base_rate_until_retire": avg_base_rate_until_retire,
        "saving_effect_years": saving_effect_years,
        "matched_income": int(pension_row["monthly_income_won"]),
        "matched_years": int(pension_row["contribution_years"]),
        "sim_df": sim_df,
        "total_needed_gap": total_needed_gap,
    }


def get_status(score):
    if score >= 80:
        return "🟢 안정", "status-good", "good"
    if score >= 60:
        return "🟡 주의", "status-warn", "warn"
    return "🔴 위험", "status-bad", "bad"


def make_insight(result, current_monthly_living_cost, retire_age):
    status_label, status_class, text_class = get_status(result["readiness_score"])
    depletion_age = result["depletion_age"]
    depletion_text = "100세 이상" if depletion_age >= 100 else f"{depletion_age}세 전후"

    if result["saving_effect_years"] > 0:
        action_sentence = f"월 저축액을 20만 원 늘리면 자산 소진 시점을 약 {result['saving_effect_years']}년 늦출 수 있습니다."
    else:
        action_sentence = "월 저축액을 늘리거나 은퇴 시점을 조정하면 100세까지의 준비율을 높일 수 있습니다."

    if result["depletion_age"] >= MAX_AGE:
        depletion_sentence = (
            "현재 자산 흐름 기준으로는 <b>100세까지 생활비 부족분을 비교적 감당할 가능성</b>이 있습니다.<br>"
            "자산 소진 예상 시점은 <b>100세 이상</b>입니다."
        )
    else:
        depletion_sentence = (
            f"현재 저축 흐름을 유지하면 은퇴 후 약 <b>{result['years_can_cover_after_retire']}년</b> 동안 생활비 부족분을 감당할 수 있습니다.<br>"
            f"자산 소진 예상 시점은 <b>{depletion_text}</b>입니다.<br>"
            f"100세까지 생활하려면 추가로 약 <b>{result['years_short']}년치</b> 자금이 부족합니다."
        )

    insight_html = textwrap.dedent(f"""
    <div class="insight-step">
        <b>1️⃣ 진단</b><br>
        노후 준비 안정도는 <b>{result['readiness_score']}점 / 100점</b>이며, 현재 준비 수준은 <span class="{text_class}">{status_label}</span> 단계입니다.
    </div>
    <div class="insight-step">
        <b>2️⃣ 미래 생활비 충격</b><br>
        현재 월 생활비 <b>{won(current_monthly_living_cost)}</b>는 은퇴 시점에 약 <b>{won(result['future_monthly_living_cost'])}</b> 수준으로 증가할 것으로 예상됩니다.<br>
        즉, 같은 생활을 유지하려면 지금보다 약 <b>{result['living_cost_multiplier']:.1f}배</b>의 생활비가 필요합니다.
    </div>
    <div class="insight-step">
        <b>3️⃣ 국민연금 의존도</b><br>
        예상 국민연금은 은퇴 후 필요 생활비의 약 <b>{result['pension_coverage']:.1f}%</b>를 충당합니다.<br>
        나머지 약 <b>{max(0, 100 - result['pension_coverage']):.1f}%</b>는 개인 자산과 저축으로 준비해야 합니다.
    </div>
    <div class="insight-step">
        <b>4️⃣ 자산 소진 시점</b><br>
        {depletion_sentence}
    </div>
    <div class="insight-step">
        <b>5️⃣ 필요한 목표 성장률</b><br>
        100세까지 현재 생활 수준을 유지하려면 자산이 매년 최소 <b>{result['required_growth']:.1f}%</b> 성장해야 합니다.<br>
        현재 기준금리 기반 평균 성장률은 약 <b>{result['avg_base_rate_until_retire']:.1f}%</b>이므로, 차이가 크다면 추가 저축이나 장기 자산 전략이 필요합니다.
    </div>
    <div class="insight-step">
        <b>6️⃣ 맞춤 행동 제안</b><br>
        {action_sentence}
    </div>
    <p style="margin-top: 20px;">
        <b>최종 해석:</b> 당신의 노후 리스크는 단순히 연금이 적다는 점보다,
        <b>물가 상승에 비해 자산 성장 속도가 충분하지 않을 수 있다는 점</b>에서 발생합니다.
        국민연금은 기본 안전망 역할을 하지만, 현재 생활 수준을 유지하려면 개인 저축과 자산 성장 전략을 함께 고려해야 합니다.
    </p>
    """).strip()

    return status_label, status_class, insight_html


# =============================
# 화면 구성
# =============================
check_db_exists()

st.markdown(
    """
    <div class="hero">
        <h1>🌱 100세 시대를 위한 데이터 기반 노후 재무 시뮬레이션 서비스</h1>
        <div class="subtitle">
            미래 물가를 반영한 개인 맞춤형 노후 대비 플랫폼입니다.<br>
            국민연금, 소비자물가지수(CPI), 기준금리 데이터를 활용해 현재의 소득·자산·저축 수준이
            미래 노후 생활을 감당할 수 있는지 분석합니다.
        </div>
        <div class="tag-row">
            <div class="tag">데이터 기반 재무 의사결정</div>
            <div class="tag">실질 노후 자산 예측</div>
            <div class="tag">CPI 반영 생활비 시뮬레이션</div>
            <div class="tag">국민연금 충당률 분석</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown("### 데이터 기반 장기 전망")
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
        color_discrete_map={"actual": "#6aaa96", "predicted": "#d8a48f"},
    )
    fig_cpi.update_layout(height=360, template="plotly_white", margin=dict(l=20, r=20, t=60, b=20))
    st.plotly_chart(fig_cpi, use_container_width=True, theme=None)
    with st.expander("사용된 SQL과 인사이트 보기"):
        st.code(sql_cpi, language="sql")
        st.info("CPI가 상승할수록 같은 생활 수준을 유지하기 위해 필요한 생활비도 증가합니다. 이 데이터는 은퇴 시점뿐 아니라 은퇴 이후 매년 생활비를 보정하는 데 사용됩니다.")

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
        color_discrete_map={"actual": "#7c83b8", "predicted": "#c9a227"},
    )
    fig_rate.update_layout(height=360, template="plotly_white", margin=dict(l=20, r=20, t=60, b=20))
    st.plotly_chart(fig_rate, use_container_width=True, theme=None)
    with st.expander("사용된 SQL과 인사이트 보기"):
        st.code(sql_rate, language="sql")
        st.info("기준금리는 자산 성장의 보수적인 기준선으로 활용됩니다. 투자수익률 대신 기준금리를 사용해 개인별 투자 성과 차이를 줄이고 객관적인 시뮬레이션 기준을 만들었습니다.")

st.divider()

st.markdown("### 내 노후 재무 시뮬레이션")
st.markdown("<div class='small-note'>월 저축액은 국민연금을 제외하고 개인적으로 모으는 저축 금액을 의미합니다.</div>", unsafe_allow_html=True)

left, right = st.columns(2)

with left:
    current_age = st.number_input("현재 나이", min_value=1, max_value=99, value=22, step=1)
    retire_age = st.number_input("은퇴 희망 나이", min_value=40, max_value=80, value=65, step=1)
    monthly_income = st.number_input("월 소득(원)", min_value=0, value=1000000, step=100000)
    current_asset = st.number_input("현재 자산(원)", min_value=0, value=7800000, step=100000)

with right:
    monthly_saving = st.number_input("개인 월 저축액(원)", min_value=0, value=400000, step=100000)
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

    status_label, status_class, insight_html = make_insight(result, current_monthly_living_cost, retire_age)

    st.markdown("### 분석 결과")

    st.markdown(f"""
    <div class="score-box">
        <div class="score-title">노후 준비 안정도 점수</div>
        <div class="score-value">{result['readiness_score']}점 <span style="font-size:1.2rem; color:#8b9099;">/ 100점</span></div>
        <span class="status-pill {status_class}">{status_label}</span>
    </div>
    """, unsafe_allow_html=True)

    m1, m2, m3, m4, m5 = st.columns(5)

    cards = [
        (m1, "은퇴 시점 예상 자산", won(result['asset_at_retirement']), "기준금리 기반 복리 + 저축 반영"),
        (m2, "은퇴 시점 월 생활비", "월 " + won(result['future_monthly_living_cost']), f"현재의 {result['living_cost_multiplier']:.1f}배"),
        (m3, "국민연금 충당률", f"{result['pension_coverage']:.1f}%", "은퇴 시점 생활비 대비"),
        (m4, "자산 소진 나이", "100세 이상" if result['depletion_age'] >= 100 else f"{result['depletion_age']}세", "은퇴 후 매년 CPI 반영"),
        (m5, "필요 성장률", f"{result['required_growth']:.1f}%", "100세까지 유지 목표"),
    ]

    for col, label, value, sub in cards:
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">{label}</div>
                <div class="metric-value">{value}</div>
                <div class="metric-sub">{sub}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    sim_df = result["sim_df"].copy()

    # 그래프 1: 자산 흐름은 억 원 단위로 표시
    sim_df["end_asset_eok"] = sim_df["end_asset"] / 100000000
    sim_df["monthly_living_cost_manwon"] = sim_df["monthly_living_cost"] / 10000
    sim_df["monthly_pension_manwon"] = sim_df["monthly_pension"] / 10000

    fig_asset = go.Figure()
    fig_asset.add_trace(go.Scatter(
        x=sim_df["age"],
        y=sim_df["end_asset_eok"],
        mode="lines+markers",
        name="예상 자산",
        line=dict(width=3, color="#6aaa96"),
    ))
    fig_asset.update_layout(
        title="은퇴 이후 예상 자산 흐름",
        xaxis_title="나이",
        yaxis_title="자산(억 원)",
        template="plotly_white",
        height=420,
        margin=dict(l=20, r=20, t=60, b=30),
        xaxis=dict(
            tickmode="linear",
            dtick=5
        )
    )

    # 그래프 2: 생활비에서 국민연금을 제외한 실제 부족분을 표시
    sim_df["monthly_gap_manwon"] = (sim_df["monthly_living_cost"] - sim_df["monthly_pension"]).clip(lower=0) / 10000

    fig_cost = go.Figure()
    fig_cost.add_trace(go.Scatter(
        x=sim_df["age"],
        y=sim_df["monthly_gap_manwon"],
        mode="lines+markers",
        name="월 생활비 부족분",
        fill="tozeroy",
        line=dict(width=3, color="#d8a48f"),
    ))
    fig_cost.update_layout(
        title="은퇴 이후 월 생활비 부족분 변화",
        xaxis_title="나이",
        yaxis_title="월 부족 금액(만 원)",
        template="plotly_white",
        height=420,
        margin=dict(l=20, r=20, t=60, b=30),
        xaxis=dict(
            tickmode="linear",
            dtick=5
        )
    )

    chart_left, chart_right = st.columns(2)
    with chart_left:
        st.plotly_chart(fig_asset, use_container_width=True, theme=None)
    with chart_right:
        st.plotly_chart(fig_cost, use_container_width=True, theme=None)

    st.markdown("### 데이터 기반 인사이트")
    insight_box_html = textwrap.dedent(f"""
    <div class="insight-box">
        <h3>진단 → 원인 → 목표 행동</h3>
        {insight_html}
        <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
        <p class="small-note">
            국민연금 조회 시 입력 소득과 가입기간에 가장 가까운 공식 표 값을 사용했습니다.<br>
            매칭된 기준소득월액: {won(result['matched_income'])}, 매칭된 가입기간: {result['matched_years']}년
        </p>
    </div>
    """).strip()

    st.markdown(insight_box_html, unsafe_allow_html=True)

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
