"""
India TB Elimination Intelligence — Streamlit Dashboard
Two datasets:
  tb_who     : WHO TB time series (Year, TB_Incidence, Treatment_Success)
  tb_tobacco : NTEP state-wise Tobacco-TB snapshot

"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from scipy.stats import linregress
import mysql.connector

st.set_page_config(page_title="India TB Tracker", page_icon="🫁", layout="wide")

# ── UPDATE YOUR PASSWORD HERE ──────────────────────────────────────────────────
MYSQL_HOST     = "localhost"
MYSQL_USER     = "root"
MYSQL_PASSWORD = "piku2005"
MYSQL_DATABASE = "tb_india"

@st.cache_resource
def get_conn():
    return mysql.connector.connect(
        host=MYSQL_HOST, user=MYSQL_USER,
        password=MYSQL_PASSWORD, database=MYSQL_DATABASE
    )

@st.cache_data
def load_who():
    df = pd.read_sql_query("SELECT * FROM tb_who ORDER BY Year", get_conn())
    df['Year'] = df['Year'].astype(int)
    return df

@st.cache_data
def load_tobacco():
    df = pd.read_sql_query("SELECT * FROM tb_tobacco", get_conn())
    df['State'] = df['State'].str.strip().str.title()
    return df

try:
    who = load_who()
    tob = load_tobacco()
    loaded = True
except Exception as e:
    st.error(f"MySQL Error: {e}")
    st.info("Make sure MySQL is running and MYSQL_PASSWORD is correct.")
    loaded = False

# ── Sidebar ────────────────────────────────────────────────────────────────────
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to:", [
    "Overview",
    "Part 1: TB Time Series",
    "Part 2: Tobacco-TB Risk",
    "Raw Data"
])
st.sidebar.markdown("---")
st.sidebar.markdown("**Project:** India TB Elimination Intelligence")
st.sidebar.markdown("**Author:** Mahasweta Talik | KIIT 2027")
st.sidebar.markdown("**Data:** WHO + NTEP India")

if not loaded:
    st.stop()

# shared helpers
def no_spine(ax):
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

national = who.dropna(subset=['TB_Incidence']).copy()
national['YoY']         = national['TB_Incidence'].diff()
national['Rolling_3yr'] = national['TB_Incidence'].rolling(window=3, center=True).mean()

baseline_2015 = national[national['Year'] == 2015]['TB_Incidence'].values[0] \
    if 2015 in national['Year'].values else national['TB_Incidence'].mean()
target_2025 = baseline_2015 * 0.10

ts_clean = national.dropna(subset=['TB_Incidence'])
slope, intercept, r2, pval, _ = linregress(ts_clean['Year'].values, ts_clean['TB_Incidence'].values)
yr_elim = int((target_2025 - intercept) / slope) if slope < 0 else 9999

# ══════════════════════════════════════════════════════════════════════════════
# OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
if page == "Overview":
    st.title("🫁 India TB Elimination Intelligence")
    st.markdown("**Tracking India's 2025 Zero-TB Target + Tobacco-TB Risk Factor Analysis**")
    st.markdown("---")

    who_first  = national.iloc[0]
    who_latest = national.iloc[-1]
    pct_drop   = (who_first['TB_Incidence'] - who_latest['TB_Incidence']) / who_first['TB_Incidence'] * 100
    prev_val   = national.iloc[-2]['TB_Incidence'] if len(national) > 1 else who_latest['TB_Incidence']

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric(f"TB Incidence ({int(who_latest['Year'])})",
              f"{who_latest['TB_Incidence']:.1f}",
              f"{who_latest['TB_Incidence'] - prev_val:.1f} vs prev yr",
              delta_color="inverse")
    c2.metric("Total Reduction", f"{pct_drop:.1f}%",
              f"{int(who_first['Year'])}→{int(who_latest['Year'])}", delta_color="normal")
    c3.metric("Years of Data",
              f"{int(who_latest['Year'] - who_first['Year'])}",
              f"{int(who_first['Year'])}–{int(who_latest['Year'])}")
    treat_latest = who.dropna(subset=['Treatment_Success'])
    if len(treat_latest) > 0:
        tv = treat_latest.iloc[-1]['Treatment_Success']
        c4.metric("Treatment Success", f"{tv:.1f}%",
                  "WHO target: 90%",
                  delta_color="normal" if tv >= 90 else "inverse")
    if 'Tobacco_TB_Total_Pct' in tob.columns:
        c5.metric("Avg Tobacco-TB %", f"{tob['Tobacco_TB_Total_Pct'].mean():.1f}%",
                  "Among TB patients")

    st.markdown("---")
    ca, cb = st.columns(2)

    with ca:
        st.subheader("National TB Incidence + 2025 Target")
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.plot(national['Year'], national['TB_Incidence'],
                color='#e63946', lw=2.5, marker='o', ms=4, label='Actual')
        ax.fill_between(national['Year'], national['TB_Incidence'], alpha=0.12, color='#e63946')
        ax.axhline(y=target_2025, color='green', ls='--', lw=1.8,
                   label=f'2025 Target ({target_2025:.0f})')
        ax.axvline(x=2025, color='orange', ls='--', lw=1.2, alpha=0.7, label='2025 Deadline')
        ax.set_xlabel('Year'); ax.set_ylabel('Incidence per 100,000')
        ax.legend(fontsize=8); no_spine(ax)
        plt.tight_layout(); st.pyplot(fig); plt.close()

    with cb:
        st.subheader("Top 10 States — Tobacco-TB Burden")
        if 'Tobacco_TB_Total_Pct' in tob.columns:
            ts = tob.dropna(subset=['Tobacco_TB_Total_Pct']).sort_values(
                'Tobacco_TB_Total_Pct', ascending=False).head(10)
            fig, ax = plt.subplots(figsize=(7, 4))
            clrs = ['#e63946' if v > ts['Tobacco_TB_Total_Pct'].mean() else '#f4a261'
                    for v in ts['Tobacco_TB_Total_Pct']]
            ax.bar(ts['State'], ts['Tobacco_TB_Total_Pct'], color=clrs, edgecolor='white', width=0.7)
            ax.axhline(y=ts['Tobacco_TB_Total_Pct'].mean(), color='navy', ls='--', lw=1.2,
                       label='Natl Avg')
            ax.set_xlabel('State'); ax.set_ylabel('% TB Patients Using Tobacco')
            ax.legend(fontsize=8); no_spine(ax)
            plt.xticks(rotation=40, ha='right', fontsize=8)
            plt.tight_layout(); st.pyplot(fig); plt.close()

    st.markdown("---")
    st.subheader("2025 Elimination Target Status")
    need = (ts_clean.iloc[-1]['TB_Incidence'] - target_2025) / max(2025 - int(ts_clean.iloc[-1]['Year']), 1)
    if yr_elim <= 2025:
        st.success(f"✅ India is ON TRACK — projected to reach elimination threshold by {yr_elim}")
    else:
        st.error(
            f"❌ India will MISS the 2025 target by ~{yr_elim - 2025} years "
            f"(projected: {yr_elim}). "
            f"Current pace: {abs(slope):.2f}/yr | Needed: {need:.2f}/yr — "
            f"must be {need/abs(slope):.1f}x faster."
        )

# ══════════════════════════════════════════════════════════════════════════════
# PART 1
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Part 1: TB Time Series":
    st.title("📈 Part 1: National TB Trend Analysis")
    st.markdown("---")

    yr_min, yr_max = int(national['Year'].min()), int(national['Year'].max())
    yr_range = st.slider("Year Range", yr_min, yr_max, (yr_min, yr_max))
    nat_f = national[(national['Year'] >= yr_range[0]) & (national['Year'] <= yr_range[1])]

    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Incidence + 2025 Target")
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.plot(nat_f['Year'], nat_f['TB_Incidence'],
                color='#e63946', lw=2.5, marker='o', ms=4)
        ax.fill_between(nat_f['Year'], nat_f['TB_Incidence'], alpha=0.12, color='#e63946')
        ax.axhline(y=target_2025, color='green', ls='--', lw=1.8,
                   label=f'2025 Target ({target_2025:.0f})')
        ax.axvline(x=2025, color='orange', ls='--', lw=1.2, label='2025 Deadline')
        ax.set_xlabel('Year'); ax.set_ylabel('per 100,000')
        ax.legend(fontsize=8); no_spine(ax)
        plt.tight_layout(); st.pyplot(fig); plt.close()

    with c2:
        st.subheader("Year-over-Year Change")
        fig, ax = plt.subplots(figsize=(7, 4))
        clrs = ['#2a9d8f' if x < 0 else '#e63946' for x in nat_f['YoY'].fillna(0)]
        ax.bar(nat_f['Year'], nat_f['YoY'], color=clrs, width=0.7, edgecolor='white')
        ax.axhline(y=0, color='black', lw=1)
        ax.set_xlabel('Year'); ax.set_ylabel('Change per 100,000')
        no_spine(ax); plt.tight_layout(); st.pyplot(fig); plt.close()
        st.caption("Green = fell that year | Red = rose that year")

    c3, c4 = st.columns(2)

    with c3:
        st.subheader("3-Year Rolling Average")
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.plot(nat_f['Year'], nat_f['TB_Incidence'],
                color='#adb5bd', lw=1.5, ls='--', alpha=0.8, label='Actual')
        ax.plot(nat_f['Year'], nat_f['Rolling_3yr'],
                color='#e63946', lw=2.8, label='3-Yr Rolling Avg')
        ax.set_xlabel('Year'); ax.set_ylabel('per 100,000')
        ax.legend(fontsize=8); no_spine(ax)
        plt.tight_layout(); st.pyplot(fig); plt.close()

    with c4:
        st.subheader("Treatment Success Rate")
        treat = who.dropna(subset=['Treatment_Success'])
        if len(treat) > 0:
            tf = treat[(treat['Year'] >= yr_range[0]) & (treat['Year'] <= yr_range[1])]
            fig, ax = plt.subplots(figsize=(7, 4))
            ax.plot(tf['Year'], tf['Treatment_Success'],
                    color='#2a9d8f', lw=2.5, marker='s', ms=5)
            ax.fill_between(tf['Year'], tf['Treatment_Success'], alpha=0.15, color='#2a9d8f')
            ax.axhline(y=90, color='green', ls='--', lw=1.8, label='WHO 90% Target')
            ax.set_ylim(0, 105); ax.set_xlabel('Year'); ax.set_ylabel('Success Rate %')
            ax.legend(fontsize=8); no_spine(ax)
            plt.tight_layout(); st.pyplot(fig); plt.close()
        else:
            st.info("Treatment Success not available in this dataset.")

    st.markdown("---")
    st.subheader("2030 Linear Projection")
    future = np.arange(int(ts_clean['Year'].min()), 2031)
    proj   = intercept + slope * future
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(ts_clean['Year'], ts_clean['TB_Incidence'],
            color='#e63946', lw=2.5, marker='o', ms=4, label='Actual')
    ax.plot(future[future > int(ts_clean['Year'].max())],
            proj[future > int(ts_clean['Year'].max())],
            color='#e63946', lw=2, ls='--', alpha=0.7, label='Projected')
    ax.axhline(y=target_2025, color='green', ls='--', lw=2,
               label=f'Elimination Target ({target_2025:.0f})')
    ax.axvline(x=2025, color='orange', ls='--', lw=1.8, label='2025 Deadline')
    ax.set_xlabel('Year'); ax.set_ylabel('TB Incidence per 100,000')
    ax.legend(fontsize=9); ax.set_xlim(ts_clean['Year'].min(), 2031); ax.set_ylim(0)
    no_spine(ax); plt.tight_layout(); st.pyplot(fig); plt.close()

    s1, s2, s3 = st.columns(3)
    s1.metric("Annual Drop Rate", f"{abs(slope):.2f} per 100k/yr")
    s2.metric("R² (trend fit)", f"{r2:.3f}")
    s3.metric("Statistically Significant", "Yes" if pval < 0.05 else "No")

# ══════════════════════════════════════════════════════════════════════════════
# PART 2
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Part 2: Tobacco-TB Risk":
    st.title("🚬 Part 2: Tobacco-TB Risk Factor Analysis")
    st.markdown("Tobacco users are **2–3× more likely** to develop TB. "
                "This section maps the tobacco burden across Indian states and cessation gaps.")
    st.markdown("---")

    c1, c2, c3, c4 = st.columns(4)
    if 'Tobacco_TB_Total_Pct' in tob.columns:
        nat_avg = tob['Tobacco_TB_Total_Pct'].mean()
        worst   = tob.dropna(subset=['Tobacco_TB_Total_Pct']).sort_values(
            'Tobacco_TB_Total_Pct', ascending=False).iloc[0]
        c1.metric("National Avg Tobacco-TB %", f"{nat_avg:.1f}%")
        c2.metric("Highest State", worst['State'], f"{worst['Tobacco_TB_Total_Pct']:.1f}%")
    if 'Tobacco_Users_Total_Count' in tob.columns and 'Cessation_Total_Count' in tob.columns:
        tu = tob['Tobacco_Users_Total_Count'].sum()
        tc = tob['Cessation_Total_Count'].sum()
        c3.metric("Total Tobacco Users Identified", f"{int(tu):,}")
        gap = (tu - tc) / tu * 100 if tu > 0 else 0
        c4.metric("National Cessation Gap", f"{gap:.1f}%",
                  "Getting NO quit support", delta_color="inverse")

    st.markdown("---")
    ca, cb = st.columns(2)

    with ca:
        st.subheader("Tobacco-TB % by State")
        if 'Tobacco_TB_Total_Pct' in tob.columns:
            ts2 = tob.dropna(subset=['Tobacco_TB_Total_Pct']).sort_values(
                'Tobacco_TB_Total_Pct', ascending=False)
            fig, ax = plt.subplots(figsize=(7, 5))
            clrs = ['#e63946' if v > ts2['Tobacco_TB_Total_Pct'].mean() else '#f4a261'
                    for v in ts2['Tobacco_TB_Total_Pct']]
            ax.bar(ts2['State'], ts2['Tobacco_TB_Total_Pct'], color=clrs, edgecolor='white', width=0.7)
            ax.axhline(y=ts2['Tobacco_TB_Total_Pct'].mean(), color='navy', ls='--', lw=1.5,
                       label='National Avg')
            ax.set_xlabel('State'); ax.set_ylabel('% TB Patients Using Tobacco')
            ax.legend(fontsize=8); no_spine(ax)
            plt.xticks(rotation=45, ha='right', fontsize=7)
            plt.tight_layout(); st.pyplot(fig); plt.close()

    with cb:
        st.subheader("Public vs Private Sector Split")
        if 'Tobacco_TB_Public_Count' in tob.columns and 'Tobacco_TB_Private_Count' in tob.columns:
            pub  = tob['Tobacco_TB_Public_Count'].sum()
            priv = tob['Tobacco_TB_Private_Count'].sum()
            fig, ax = plt.subplots(figsize=(7, 5))
            ax.pie([pub, priv], labels=['Public', 'Private'],
                   autopct='%1.1f%%', colors=['#457b9d', '#f4a261'],
                   startangle=90, textprops={'fontsize': 13})
            ax.set_title('Where Are Tobacco-TB Patients Seen?', fontweight='bold')
            plt.tight_layout(); st.pyplot(fig); plt.close()

    cc, cd = st.columns(2)

    with cc:
        st.subheader("Cessation Coverage Gap by State")
        st.caption("% of tobacco-using TB patients NOT linked to quit-smoking support")
        if 'Tobacco_Users_Total_Count' in tob.columns and 'Cessation_Total_Count' in tob.columns:
            tg = tob.dropna(subset=['Tobacco_Users_Total_Count', 'Cessation_Total_Count']).copy()
            tg['gap_pct'] = ((tg['Tobacco_Users_Total_Count'] - tg['Cessation_Total_Count'])
                              / tg['Tobacco_Users_Total_Count'] * 100).round(1)
            tg = tg.sort_values('gap_pct', ascending=False)
            fig, ax = plt.subplots(figsize=(7, 5))
            ax.bar(tg['State'], tg['gap_pct'], color='#8338ec', edgecolor='white', width=0.7)
            ax.axhline(y=tg['gap_pct'].mean(), color='red', ls='--', lw=1.5, label='Natl Avg Gap')
            ax.set_xlabel('State'); ax.set_ylabel('% Not Getting Support')
            ax.legend(fontsize=8); no_spine(ax)
            plt.xticks(rotation=45, ha='right', fontsize=7)
            plt.tight_layout(); st.pyplot(fig); plt.close()

    with cd:
        st.subheader("Identified vs Linked to Support")
        if 'Tobacco_Users_Total_Count' in tob.columns and 'Cessation_Total_Count' in tob.columns:
            tc2 = tob.dropna(subset=['Tobacco_Users_Total_Count', 'Cessation_Total_Count']).sort_values(
                'Tobacco_Users_Total_Count', ascending=False).head(12)
            x = range(len(tc2))
            fig, ax = plt.subplots(figsize=(7, 5))
            ax.bar([i - 0.2 for i in x], tc2['Tobacco_Users_Total_Count'],
                   width=0.35, label='Identified', color='#457b9d', edgecolor='white')
            ax.bar([i + 0.2 for i in x], tc2['Cessation_Total_Count'],
                   width=0.35, label='Linked to Support', color='#2a9d8f', edgecolor='white')
            ax.set_xticks(list(x))
            ax.set_xticklabels(tc2['State'], rotation=45, ha='right', fontsize=7)
            ax.set_ylabel('Count'); ax.legend(fontsize=8); no_spine(ax)
            plt.tight_layout(); st.pyplot(fig); plt.close()
            st.caption("Gap between blue and green = patients falling through the cracks")

    st.markdown("---")
    st.subheader("State Priority Classification")
    if 'Tobacco_TB_Total_Pct' in tob.columns:
        tob_cls = tob.dropna(subset=['Tobacco_TB_Total_Pct']).copy()
        if 'Tobacco_Users_Total_Count' in tob_cls.columns and 'Cessation_Total_Count' in tob_cls.columns:
            tob_cls['Cessation_Gap_%'] = ((
                tob_cls['Tobacco_Users_Total_Count'] - tob_cls['Cessation_Total_Count']
            ) / tob_cls['Tobacco_Users_Total_Count'] * 100).round(1)
        def classify(row):
            t = row.get('Tobacco_TB_Total_Pct') or 0
            g = row.get('Cessation_Gap_%') or 0
            if t >= 50 and g >= 50: return '🔴 HIGH RISK'
            elif t >= 50:           return '🟠 HIGH TOBACCO'
            elif g >= 50:           return '🟡 POOR CESSATION'
            return '🟢 LOW RISK'
        tob_cls['Priority'] = tob_cls.apply(classify, axis=1)
        dcols = [c for c in ['State', 'Tobacco_TB_Total_Pct', 'Cessation_Gap_%', 'Priority']
                 if c in tob_cls.columns]
        st.dataframe(
            tob_cls[dcols].rename(columns={'Tobacco_TB_Total_Pct': 'Tobacco-TB %'})
                          .sort_values('Tobacco-TB %', ascending=False),
            use_container_width=True, height=380
        )

# ══════════════════════════════════════════════════════════════════════════════
# RAW DATA
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Raw Data":
    st.title("📋 Raw Data")
    st.markdown("---")
    t1, t2 = st.tabs(["WHO TB Time Series (tb_who)", "Tobacco-TB State Data (tb_tobacco)"])
    with t1:
        st.dataframe(who, use_container_width=True, height=400)
        st.download_button("Download CSV", who.to_csv(index=False), "tb_who.csv", "text/csv")
    with t2:
        st.dataframe(tob, use_container_width=True, height=400)
        st.download_button("Download CSV", tob.to_csv(index=False), "tb_tobacco.csv", "text/csv")

st.markdown("---")
st.markdown("**India TB Elimination Intelligence** | Data: WHO + NTEP India | "
            "Mahasweta Talik — KIIT University 2027 | Python · MySQL · Streamlit")
