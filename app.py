import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pybaseball as pb

pb.cache.enable()

st.set_page_config(
    page_title="Baseball Analytics",
    page_icon="⚾",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
}

.stApp {
    background-color: #0d1117;
    color: #e6edf3;
}

section[data-testid="stSidebar"] {
    background-color: #161b22;
    border-right: 1px solid #21262d;
}

section[data-testid="stSidebar"] * {
    color: #c9d1d9 !important;
}

h1, h2, h3 {
    font-family: 'IBM Plex Mono', monospace !important;
    color: #e6edf3 !important;
    letter-spacing: -0.02em;
}

.stat-card {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 8px;
    padding: 16px 20px;
    text-align: center;
}

.stat-value {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 28px;
    font-weight: 600;
    color: #58a6ff;
    line-height: 1.1;
}

.stat-label {
    font-size: 11px;
    color: #8b949e;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-top: 4px;
}

.stat-sub {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 12px;
    color: #3fb950;
    margin-top: 2px;
}

.section-header {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 11px;
    color: #8b949e;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    border-bottom: 1px solid #21262d;
    padding-bottom: 8px;
    margin-bottom: 16px;
}

.player-tag {
    display: inline-block;
    background: #1f3a5f;
    color: #58a6ff;
    font-size: 12px;
    font-family: 'IBM Plex Mono', monospace;
    padding: 3px 10px;
    border-radius: 20px;
    margin-right: 6px;
}

div[data-testid="stSelectbox"] label,
div[data-testid="stMultiSelect"] label,
div[data-testid="stSlider"] label {
    color: #8b949e !important;
    font-size: 12px !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}

.stButton > button {
    background: #1f3a5f;
    color: #58a6ff;
    border: 1px solid #1f6feb;
    border-radius: 6px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 13px;
}

.stButton > button:hover {
    background: #1f6feb;
    color: #ffffff;
}

div[data-testid="stMetric"] {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 8px;
    padding: 12px 16px;
}

div[data-testid="stMetricValue"] {
    font-family: 'IBM Plex Mono', monospace !important;
    color: #58a6ff !important;
}

div[data-testid="stMetricDelta"] { color: #3fb950 !important; }

.stTabs [data-baseweb="tab-list"] {
    background-color: #161b22;
    border-bottom: 1px solid #21262d;
}

.stTabs [data-baseweb="tab"] {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 13px;
    color: #8b949e;
}

.stTabs [aria-selected="true"] {
    color: #58a6ff !important;
}

.stDataFrame { border: 1px solid #21262d; border-radius: 8px; }

.block-container { padding-top: 2rem; }
</style>
""", unsafe_allow_html=True)

PLOT_THEME = dict(
    paper_bgcolor="#0d1117",
    plot_bgcolor="#0d1117",
    font_color="#c9d1d9",
    font_family="IBM Plex Sans",
    colorway=["#58a6ff", "#3fb950", "#f0883e", "#d2a8ff", "#ffa657", "#79c0ff"],
    xaxis=dict(gridcolor="#21262d", linecolor="#30363d", tickcolor="#30363d"),
    yaxis=dict(gridcolor="#21262d", linecolor="#30363d", tickcolor="#30363d"),
)

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚾ Baseball Analytics")
    st.markdown("---")

    mode = st.radio(
        "Dashboard mode",
        ["Batting", "Pitching", "Player Comparison"],
        index=0,
    )

    st.markdown("---")

    year = st.selectbox("Season", list(range(2024, 2014, -1)), index=0)

    if mode in ["Batting", "Player Comparison"]:
        min_pa = st.slider("Min. plate appearances", 50, 400, 150, step=25)

    if mode in ["Pitching", "Player Comparison"]:
        min_ip = st.slider("Min. innings pitched", 10, 150, 50, step=10)

    st.markdown("---")
    st.markdown(
        "<div style='font-size:11px;color:#8b949e;'>Data via pybaseball · Baseball Reference & FanGraphs</div>",
        unsafe_allow_html=True,
    )


# ── Data loaders ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def load_batting(season: int, min_pa: int) -> pd.DataFrame:
    df = pb.batting_stats(season, qual=min_pa)
    df = df.dropna(subset=["AVG", "OBP", "SLG", "HR", "RBI", "BB%", "K%", "wRC+", "WAR", "Name", "Team"])
    df["OPS"] = df["OBP"] + df["SLG"]
    df["BB%_num"] = df["BB%"].astype(str).str.replace("%", "").astype(float)
    df["K%_num"] = df["K%"].astype(str).str.replace("%", "").astype(float)
    return df.reset_index(drop=True)


@st.cache_data(ttl=3600, show_spinner=False)
def load_pitching(season: int, min_ip: int) -> pd.DataFrame:
    df = pb.pitching_stats(season, qual=min_ip)
    needed = ["Name", "Team", "ERA", "FIP", "xFIP", "WHIP", "K/9", "BB/9", "HR/9", "WAR", "IP", "K%", "BB%"]
    df = df.dropna(subset=[c for c in needed if c in df.columns])
    df["BB%_num"] = df["BB%"].astype(str).str.replace("%", "").astype(float)
    df["K%_num"] = df["K%"].astype(str).str.replace("%", "").astype(float)
    return df.reset_index(drop=True)


def fmt(val, decimals=3):
    if pd.isna(val):
        return "–"
    return f"{val:.{decimals}f}"


# ══════════════════════════════════════════════════════════════════════════════
#  BATTING
# ══════════════════════════════════════════════════════════════════════════════
if mode == "Batting":
    st.markdown(f"# Batting Dashboard · {year}")

    with st.spinner("Loading batting data…"):
        df = load_batting(year, min_pa)

    if df.empty:
        st.error("No data available for this season / filter combo.")
        st.stop()

    # KPI row
    c1, c2, c3, c4, c5 = st.columns(5)
    top_avg = df.loc[df["AVG"].idxmax()]
    top_hr  = df.loc[df["HR"].idxmax()]
    top_ops = df.loc[df["OPS"].idxmax()]
    top_war = df.loc[df["WAR"].idxmax()]
    top_rbi = df.loc[df["RBI"].idxmax()]

    for col, label, val, player in [
        (c1, "League AVG", f"{df['AVG'].mean():.3f}", ""),
        (c2, "HR leader",  str(int(top_hr["HR"])),   top_hr["Name"]),
        (c3, "Best OPS",   f"{top_ops['OPS']:.3f}",  top_ops["Name"]),
        (c4, "Best WAR",   f"{top_war['WAR']:.1f}",  top_war["Name"]),
        (c5, "RBI leader", str(int(top_rbi["RBI"])), top_rbi["Name"]),
    ]:
        with col:
            st.markdown(
                f'<div class="stat-card"><div class="stat-value">{val}</div>'
                f'<div class="stat-label">{label}</div>'
                f'<div class="stat-sub">{player}</div></div>',
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["Scatter explorer", "Top 20 leaderboard", "Team breakdown", "K% vs BB%"])

    with tab1:
        st.markdown('<div class="section-header">Interactive scatter — click players to explore</div>', unsafe_allow_html=True)
        cx, cy = st.columns(2)
        batting_metrics = ["AVG", "OBP", "SLG", "OPS", "HR", "RBI", "BB%_num", "K%_num", "wRC+", "WAR"]
        x_axis = cx.selectbox("X axis", batting_metrics, index=9)
        y_axis = cy.selectbox("Y axis", batting_metrics, index=8)

        fig = px.scatter(
            df, x=x_axis, y=y_axis, color="Team",
            hover_name="Name",
            hover_data={"AVG": ":.3f", "HR": True, "OPS": ":.3f", "WAR": ":.1f"},
            size="PA" if "PA" in df.columns else None,
            size_max=18,
            labels={x_axis: x_axis, y_axis: y_axis},
        )
        fig.update_layout(**PLOT_THEME, height=480, showlegend=False,
                          margin=dict(l=0, r=0, t=20, b=0))
        fig.update_traces(marker=dict(opacity=0.75, line=dict(width=0.5, color="#0d1117")))
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.markdown('<div class="section-header">Top 20 by wRC+</div>', unsafe_allow_html=True)
        top20 = df.nlargest(20, "wRC+")[["Name", "Team", "PA", "AVG", "OBP", "SLG", "OPS", "HR", "RBI", "wRC+", "WAR"]]

        fig = px.bar(
            top20.sort_values("wRC+"),
            x="wRC+", y="Name", orientation="h",
            color="wRC+", color_continuous_scale=["#1f3a5f", "#58a6ff", "#cae8ff"],
            hover_data={"AVG": ":.3f", "HR": True, "WAR": ":.1f"},
        )
        fig.update_layout(**PLOT_THEME, height=540, coloraxis_showscale=False,
                          margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(
            top20.reset_index(drop=True),
            use_container_width=True,
            hide_index=True,
            column_config={
                "AVG": st.column_config.NumberColumn(format="%.3f"),
                "OBP": st.column_config.NumberColumn(format="%.3f"),
                "SLG": st.column_config.NumberColumn(format="%.3f"),
                "OPS": st.column_config.NumberColumn(format="%.3f"),
                "WAR": st.column_config.NumberColumn(format="%.1f"),
            },
        )

    with tab3:
        st.markdown('<div class="section-header">Team batting averages</div>', unsafe_allow_html=True)
        team_stats = df.groupby("Team").agg(
            AVG=("AVG", "mean"),
            OPS=("OPS", "mean"),
            HR=("HR", "sum"),
            wRC_plus=("wRC+", "mean"),
            Players=("Name", "count"),
        ).round(3).sort_values("OPS", ascending=False).reset_index()

        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=["Team OPS", "Team HR total"],
        )
        fig.add_trace(
            go.Bar(x=team_stats["Team"], y=team_stats["OPS"],
                   marker_color="#58a6ff", name="OPS"), row=1, col=1
        )
        fig.add_trace(
            go.Bar(x=team_stats["Team"], y=team_stats["HR"],
                   marker_color="#3fb950", name="HR"), row=1, col=2
        )
        fig.update_layout(**PLOT_THEME, height=400, showlegend=False,
                          margin=dict(l=0, r=0, t=40, b=0))
        fig.update_xaxes(tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

    with tab4:
        st.markdown('<div class="section-header">Plate discipline — K% vs BB%</div>', unsafe_allow_html=True)
        fig = px.scatter(
            df, x="BB%_num", y="K%_num",
            color="wRC+", color_continuous_scale=["#1f3a5f", "#58a6ff", "#cae8ff"],
            hover_name="Name",
            hover_data={"AVG": ":.3f", "HR": True, "wRC+": True},
            labels={"BB%_num": "BB%", "K%_num": "K%"},
        )
        avg_bb = df["BB%_num"].mean()
        avg_k  = df["K%_num"].mean()
        fig.add_hline(y=avg_k,  line_dash="dot", line_color="#8b949e", annotation_text="Avg K%")
        fig.add_vline(x=avg_bb, line_dash="dot", line_color="#8b949e", annotation_text="Avg BB%")
        fig.update_layout(**PLOT_THEME, height=460, margin=dict(l=0, r=0, t=20, b=0))
        st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
#  PITCHING
# ══════════════════════════════════════════════════════════════════════════════
elif mode == "Pitching":
    st.markdown(f"# Pitching Dashboard · {year}")

    with st.spinner("Loading pitching data…"):
        df = load_pitching(year, min_ip)

    if df.empty:
        st.error("No data available for this season / filter combo.")
        st.stop()

    c1, c2, c3, c4, c5 = st.columns(5)
    top_era = df.loc[df["ERA"].idxmin()]
    top_war = df.loc[df["WAR"].idxmax()]
    top_k   = df.loc[df["K/9"].idxmax()]
    top_fip = df.loc[df["FIP"].idxmin()]
    top_whi = df.loc[df["WHIP"].idxmin()]

    for col, label, val, player in [
        (c1, "Lg. ERA",    f"{df['ERA'].mean():.2f}",  ""),
        (c2, "Best ERA",   f"{top_era['ERA']:.2f}",    top_era["Name"]),
        (c3, "Best WAR",   f"{top_war['WAR']:.1f}",    top_war["Name"]),
        (c4, "K/9 leader", f"{top_k['K/9']:.1f}",      top_k["Name"]),
        (c5, "Best FIP",   f"{top_fip['FIP']:.2f}",    top_fip["Name"]),
    ]:
        with col:
            st.markdown(
                f'<div class="stat-card"><div class="stat-value">{val}</div>'
                f'<div class="stat-label">{label}</div>'
                f'<div class="stat-sub">{player}</div></div>',
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["ERA vs FIP", "Top 20 starters", "K% vs BB%"])

    with tab1:
        st.markdown('<div class="section-header">ERA vs FIP — luck vs skill</div>', unsafe_allow_html=True)
        st.markdown(
            '<p style="font-size:12px;color:#8b949e">Pitchers above the line are outperforming their FIP (lucky); below = unlucky or regressing.</p>',
            unsafe_allow_html=True,
        )
        fig = px.scatter(
            df, x="FIP", y="ERA", color="WAR",
            color_continuous_scale=["#f0883e", "#8b949e", "#3fb950"],
            hover_name="Name",
            hover_data={"IP": ":.0f", "K/9": ":.2f", "WHIP": ":.2f", "WAR": ":.1f"},
        )
        mn = min(df["FIP"].min(), df["ERA"].min()) - 0.2
        mx = max(df["FIP"].max(), df["ERA"].max()) + 0.2
        fig.add_shape(type="line", x0=mn, y0=mn, x1=mx, y1=mx,
                      line=dict(color="#8b949e", dash="dot", width=1))
        fig.update_layout(**PLOT_THEME, height=460, margin=dict(l=0, r=0, t=20, b=0))
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.markdown('<div class="section-header">Top 20 by WAR</div>', unsafe_allow_html=True)
        cols_show = [c for c in ["Name", "Team", "IP", "ERA", "FIP", "xFIP", "WHIP", "K/9", "BB/9", "WAR"] if c in df.columns]
        top20 = df.nlargest(20, "WAR")[cols_show]

        fig = px.bar(
            top20.sort_values("WAR"),
            x="WAR", y="Name", orientation="h",
            color="ERA", color_continuous_scale=["#3fb950", "#58a6ff", "#f0883e"],
            hover_data={c: True for c in ["ERA", "FIP", "K/9"]},
        )
        fig.update_layout(**PLOT_THEME, height=540, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig, use_container_width=True)

        fmt_cfg = {c: st.column_config.NumberColumn(format="%.2f")
                   for c in ["ERA", "FIP", "xFIP", "WHIP", "K/9", "BB/9", "WAR", "IP"]}
        st.dataframe(top20.reset_index(drop=True), use_container_width=True,
                     hide_index=True, column_config=fmt_cfg)

    with tab3:
        st.markdown('<div class="section-header">Pitcher plate discipline</div>', unsafe_allow_html=True)
        fig = px.scatter(
            df, x="BB%_num", y="K%_num",
            color="ERA", color_continuous_scale=["#3fb950", "#8b949e", "#f0883e"],
            hover_name="Name",
            hover_data={"ERA": ":.2f", "FIP": ":.2f", "WAR": ":.1f"},
            labels={"BB%_num": "BB%", "K%_num": "K%"},
        )
        fig.add_hline(y=df["K%_num"].mean(),  line_dash="dot", line_color="#8b949e", annotation_text="Avg K%")
        fig.add_vline(x=df["BB%_num"].mean(), line_dash="dot", line_color="#8b949e", annotation_text="Avg BB%")
        fig.update_layout(**PLOT_THEME, height=460, margin=dict(l=0, r=0, t=20, b=0))
        st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
#  PLAYER COMPARISON
# ══════════════════════════════════════════════════════════════════════════════
elif mode == "Player Comparison":
    st.markdown(f"# Player Comparison · {year}")

    comp_type = st.radio("Compare", ["Batters", "Pitchers"], horizontal=True)

    if comp_type == "Batters":
        with st.spinner("Loading batting data…"):
            df = load_batting(year, min_pa)

        players = st.multiselect(
            "Select players (2–6)",
            sorted(df["Name"].tolist()),
            default=df.nlargest(4, "WAR")["Name"].tolist()[:4],
            max_selections=6,
        )

        if len(players) < 2:
            st.info("Select at least 2 players to compare.")
            st.stop()

        sel = df[df["Name"].isin(players)].copy()

        metrics = ["AVG", "OBP", "SLG", "OPS", "wRC+", "WAR", "HR", "RBI"]
        radar_metrics = ["AVG", "OBP", "SLG", "wRC+", "WAR"]

        fig = go.Figure()
        for _, row in sel.iterrows():
            vals = [row[m] for m in radar_metrics]
            fig.add_trace(go.Scatterpolar(
                r=vals + [vals[0]],
                theta=radar_metrics + [radar_metrics[0]],
                fill="toself", name=row["Name"], opacity=0.6,
            ))
        fig.update_layout(
            **PLOT_THEME, height=420,
            polar=dict(
                bgcolor="#161b22",
                radialaxis=dict(visible=True, gridcolor="#21262d", color="#8b949e"),
                angularaxis=dict(gridcolor="#21262d", color="#c9d1d9"),
            ),
            showlegend=True,
            margin=dict(l=60, r=60, t=40, b=40),
        )
        st.plotly_chart(fig, use_container_width=True)

        display_cols = ["Name", "Team"] + metrics
        display_cols = [c for c in display_cols if c in sel.columns]
        st.dataframe(
            sel[display_cols].reset_index(drop=True),
            use_container_width=True, hide_index=True,
            column_config={
                "AVG": st.column_config.NumberColumn(format="%.3f"),
                "OBP": st.column_config.NumberColumn(format="%.3f"),
                "SLG": st.column_config.NumberColumn(format="%.3f"),
                "OPS": st.column_config.NumberColumn(format="%.3f"),
                "WAR": st.column_config.NumberColumn(format="%.1f"),
            },
        )

    else:
        with st.spinner("Loading pitching data…"):
            df = load_pitching(year, min_ip)

        players = st.multiselect(
            "Select pitchers (2–6)",
            sorted(df["Name"].tolist()),
            default=df.nlargest(4, "WAR")["Name"].tolist()[:4],
            max_selections=6,
        )

        if len(players) < 2:
            st.info("Select at least 2 pitchers to compare.")
            st.stop()

        sel = df[df["Name"].isin(players)].copy()

        radar_metrics = ["K/9", "BB/9", "WAR", "ERA", "WHIP"]
        fig = go.Figure()
        for _, row in sel.iterrows():
            vals = [row[m] for m in radar_metrics if m in sel.columns]
            fig.add_trace(go.Scatterpolar(
                r=vals + [vals[0]],
                theta=radar_metrics + [radar_metrics[0]],
                fill="toself", name=row["Name"], opacity=0.6,
            ))
        fig.update_layout(
            **PLOT_THEME, height=420,
            polar=dict(
                bgcolor="#161b22",
                radialaxis=dict(visible=True, gridcolor="#21262d", color="#8b949e"),
                angularaxis=dict(gridcolor="#21262d", color="#c9d1d9"),
            ),
            showlegend=True,
            margin=dict(l=60, r=60, t=40, b=40),
        )
        st.plotly_chart(fig, use_container_width=True)

        pcols = [c for c in ["Name", "Team", "IP", "ERA", "FIP", "xFIP", "WHIP", "K/9", "BB/9", "WAR"] if c in sel.columns]
        st.dataframe(
            sel[pcols].reset_index(drop=True),
            use_container_width=True, hide_index=True,
            column_config={c: st.column_config.NumberColumn(format="%.2f")
                           for c in ["ERA", "FIP", "xFIP", "WHIP", "K/9", "BB/9", "WAR", "IP"]},
        )
