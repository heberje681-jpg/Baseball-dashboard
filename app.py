"""
⚾ Baseball Analytics — Real-Time 2026
Source: MLB Official Stats API (statsapi.mlb.com) — FREE, no API key
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests, datetime

st.set_page_config(page_title="⚾ MLB Analytics", page_icon="⚾", layout="wide")

# ── Styles ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;500&display=swap');
html,body,[class*="css"]{font-family:'IBM Plex Sans',sans-serif;}
.stApp{background:#0d1117;color:#e6edf3;}
section[data-testid="stSidebar"]{background:#161b22;border-right:1px solid #21262d;}
section[data-testid="stSidebar"] *{color:#c9d1d9!important;}
h1,h2,h3{font-family:'IBM Plex Mono',monospace!important;color:#e6edf3!important;letter-spacing:-.02em;}
.kpi{background:#161b22;border:1px solid #21262d;border-radius:8px;padding:14px 18px;text-align:center;}
.kpi-val{font-family:'IBM Plex Mono',monospace;font-size:26px;font-weight:600;color:#58a6ff;}
.kpi-lbl{font-size:11px;color:#8b949e;text-transform:uppercase;letter-spacing:.08em;margin-top:3px;}
.kpi-sub{font-family:'IBM Plex Mono',monospace;font-size:11px;color:#3fb950;margin-top:2px;}
.sec{font-family:'IBM Plex Mono',monospace;font-size:11px;color:#8b949e;text-transform:uppercase;letter-spacing:.1em;border-bottom:1px solid #21262d;padding-bottom:6px;margin-bottom:14px;}
.stTabs [data-baseweb="tab-list"]{background:#161b22;border-bottom:1px solid #21262d;}
.stTabs [data-baseweb="tab"]{font-family:'IBM Plex Mono',monospace;font-size:12px;color:#8b949e;}
.stTabs [aria-selected="true"]{color:#58a6ff!important;}
.block-container{padding-top:1.5rem;}
div[data-testid="stSelectbox"] label,div[data-testid="stSlider"] label,div[data-testid="stMultiSelect"] label{color:#8b949e!important;font-size:11px!important;text-transform:uppercase;letter-spacing:.06em;}
</style>""", unsafe_allow_html=True)

PT = dict(paper_bgcolor="#0d1117", plot_bgcolor="#0d1117", font_color="#c9d1d9",
          font_family="IBM Plex Sans",
          colorway=["#58a6ff","#3fb950","#f0883e","#d2a8ff","#ffa657","#79c0ff"],
          xaxis=dict(gridcolor="#21262d",linecolor="#30363d"),
          yaxis=dict(gridcolor="#21262d",linecolor="#30363d"))

BASE = "https://statsapi.mlb.com/api/v1"
SEASON = 2026

# ── Data helpers ──────────────────────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def get(url, params=None):
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return None

@st.cache_data(ttl=300, show_spinner=False)
def load_hitting_leaders(limit=150):
    rows = []
    for group in ["hitting"]:
        data = get(f"{BASE}/stats/leaders", {
            "leaderCategories": "battingAverage,homeRuns,rbi,onBasePlusSlugging,stolenBases,hits,walks,strikeouts",
            "season": SEASON, "sportId": 1, "limit": limit,
            "statGroup": group, "gameType": "R"
        })
        if not data: return pd.DataFrame()
        for cat in data.get("leagueLeaders", []):
            cat_name = cat.get("leaderCategory","")
            for entry in cat.get("leaders", []):
                rows.append({
                    "Name":    entry.get("person",{}).get("fullName",""),
                    "Team":    entry.get("team",{}).get("name",""),
                    "TeamAbb": entry.get("team",{}).get("abbreviation",""),
                    "Rank":    entry.get("rank",0),
                    "Stat":    cat_name,
                    "Value":   entry.get("value","0"),
                })
    return pd.DataFrame(rows)

@st.cache_data(ttl=300, show_spinner=False)
def load_pitching_leaders(limit=100):
    rows = []
    data = get(f"{BASE}/stats/leaders", {
        "leaderCategories": "earnedRunAverage,strikeouts,wins,whip,saves,inningsPitched",
        "season": SEASON, "sportId": 1, "limit": limit,
        "statGroup": "pitching", "gameType": "R"
    })
    if not data: return pd.DataFrame()
    for cat in data.get("leagueLeaders", []):
        cat_name = cat.get("leaderCategory","")
        for entry in cat.get("leaders", []):
            rows.append({
                "Name":    entry.get("person",{}).get("fullName",""),
                "Team":    entry.get("team",{}).get("name",""),
                "TeamAbb": entry.get("team",{}).get("abbreviation",""),
                "Rank":    entry.get("rank",0),
                "Stat":    cat_name,
                "Value":   entry.get("value","0"),
            })
    return pd.DataFrame(rows)

@st.cache_data(ttl=300, show_spinner=False)
def load_standings():
    data = get(f"{BASE}/standings", {"leagueId":"103,104","season":SEASON,"standingsTypes":"regularSeason"})
    if not data: return pd.DataFrame()
    rows = []
    for rec in data.get("records",[]):
        div = rec.get("division",{}).get("name","")
        for t in rec.get("teamRecords",[]):
            rows.append({
                "Division": div,
                "Team":     t.get("team",{}).get("name",""),
                "W":        t.get("wins",0),
                "L":        t.get("losses",0),
                "Pct":      float(t.get("winningPercentage",0)),
                "GB":       t.get("gamesBack","–"),
                "RS":       t.get("runsScored",0),
                "RA":       t.get("runsAllowed",0),
                "Streak":   t.get("streak",{}).get("streakCode",""),
                "L10":      t.get("records",{}).get("splitRecords",[{}])[0].get("wins","") if t.get("records",{}).get("splitRecords") else "",
            })
    return pd.DataFrame(rows)

@st.cache_data(ttl=60, show_spinner=False)
def load_today_games():
    today = datetime.date.today().strftime("%Y-%m-%d")
    data = get(f"{BASE}/schedule", {"sportId":1,"date":today,"hydrate":"linescore,team"})
    if not data: return []
    games = []
    for date in data.get("dates",[]):
        for g in date.get("games",[]):
            status = g.get("status",{}).get("detailedState","")
            away = g.get("teams",{}).get("away",{})
            home = g.get("teams",{}).get("home",{})
            games.append({
                "Status":    status,
                "Away":      away.get("team",{}).get("name",""),
                "AwayScore": away.get("score","–"),
                "Home":      home.get("team",{}).get("name",""),
                "HomeScore": home.get("score","–"),
                "Inning":    g.get("linescore",{}).get("currentInningOrdinal",""),
                "Venue":     g.get("venue",{}).get("name",""),
            })
    return games

def pivot_leaders(df, stat):
    sub = df[df["Stat"]==stat].copy()
    sub["Value"] = pd.to_numeric(sub["Value"], errors="coerce")
    return sub.dropna(subset=["Value"]).sort_values("Value", ascending=False).head(20)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚾ MLB Analytics")
    st.markdown(f"**Season {SEASON} · Live data**")
    st.markdown("---")
    mode = st.radio("View", ["🏆 Standings","🏏 Batting leaders","⚾ Pitching leaders","📅 Today's games","🔀 Compare players"])
    st.markdown("---")
    st.markdown('<div style="font-size:10px;color:#8b949e;">Source: MLB Official Stats API<br>Updates every 5 min</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# STANDINGS
# ══════════════════════════════════════════════════════════════════════════════
if "Standings" in mode:
    st.markdown(f"# MLB Standings · {SEASON}")
    with st.spinner("Fetching live standings…"):
        df = load_standings()
    if df.empty:
        st.error("Could not reach MLB API. Try again in a moment.")
        st.stop()

    updated = datetime.datetime.now().strftime("%H:%M:%S")
    st.caption(f"Last updated: {updated}")

    league = st.radio("League", ["American League","National League"], horizontal=True)
    al_divs = ["American League West","American League East","American League Central"]
    nl_divs = ["National League West","National League East","National League Central"]
    divs = al_divs if "American" in league else nl_divs

    cols = st.columns(3)
    for i, div in enumerate(divs):
        sub = df[df["Division"]==div].sort_values("Pct", ascending=False)
        with cols[i]:
            st.markdown(f'<div class="sec">{div.split()[-1]} Division</div>', unsafe_allow_html=True)
            if sub.empty:
                st.info("No data")
                continue
            for _, row in sub.iterrows():
                pct_bar = "█" * int(row["Pct"]*10) + "░" * (10-int(row["Pct"]*10))
                st.markdown(f"""
                <div style="background:#161b22;border:1px solid #21262d;border-radius:6px;padding:10px 14px;margin-bottom:8px;">
                  <div style="font-family:'IBM Plex Mono',monospace;font-size:13px;color:#e6edf3;font-weight:500;">{row['Team']}</div>
                  <div style="font-family:'IBM Plex Mono',monospace;font-size:11px;color:#58a6ff;margin-top:2px;">{row['W']}-{row['L']} &nbsp;·&nbsp; .{str(int(row['Pct']*1000)).zfill(3)} &nbsp;·&nbsp; GB: {row['GB']}</div>
                  <div style="font-size:10px;color:#3fb950;margin-top:2px;">{pct_bar} &nbsp;{row['Streak']}</div>
                </div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<div class="sec">Run differential by team</div>', unsafe_allow_html=True)
    df["RunDiff"] = df["RS"] - df["RA"]
    fig = px.bar(df.sort_values("RunDiff", ascending=False),
                 x="Team", y="RunDiff", color="RunDiff",
                 color_continuous_scale=["#f0883e","#8b949e","#3fb950"])
    fig.add_hline(y=0, line_color="#8b949e", line_width=1)
    fig.update_layout(**PT, height=350, coloraxis_showscale=False, margin=dict(l=0,r=0,t=10,b=0))
    fig.update_xaxes(tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# BATTING LEADERS
# ══════════════════════════════════════════════════════════════════════════════
elif "Batting" in mode:
    st.markdown(f"# Batting Leaders · {SEASON}")
    with st.spinner("Fetching live batting stats…"):
        df = load_hitting_leaders()
    if df.empty:
        st.error("Could not reach MLB API.")
        st.stop()
    st.caption(f"Updated: {datetime.datetime.now().strftime('%H:%M:%S')} · Top 150 qualified batters")

    stat_map = {
        "Batting Average":"battingAverage",
        "Home Runs":"homeRuns",
        "RBI":"rbi",
        "OPS":"onBasePlusSlugging",
        "Stolen Bases":"stolenBases",
        "Hits":"hits",
        "Walks":"walks",
        "Strikeouts":"strikeouts",
    }
    chosen = st.selectbox("Stat category", list(stat_map.keys()))
    top = pivot_leaders(df, stat_map[chosen])

    c1,c2,c3 = st.columns(3)
    for col, i in zip([c1,c2,c3],[0,1,2]):
        if i < len(top):
            row = top.iloc[i]
            with col:
                st.markdown(f'<div class="kpi"><div class="kpi-val">{row["Value"]}</div><div class="kpi-lbl">#{i+1} {chosen}</div><div class="kpi-sub">{row["Name"]} · {row["TeamAbb"]}</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    fig = px.bar(top.sort_values("Value"), x="Value", y="Name", orientation="h",
                 color="Value", color_continuous_scale=["#1f3a5f","#58a6ff","#cae8ff"],
                 hover_data={"Team":True})
    fig.update_layout(**PT, height=520, coloraxis_showscale=False, margin=dict(l=0,r=0,t=10,b=0))
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("Full table"):
        st.dataframe(top[["Rank","Name","Team","Value"]].reset_index(drop=True),
                     use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# PITCHING LEADERS
# ══════════════════════════════════════════════════════════════════════════════
elif "Pitching" in mode:
    st.markdown(f"# Pitching Leaders · {SEASON}")
    with st.spinner("Fetching live pitching stats…"):
        df = load_pitching_leaders()
    if df.empty:
        st.error("Could not reach MLB API.")
        st.stop()
    st.caption(f"Updated: {datetime.datetime.now().strftime('%H:%M:%S')}")

    stat_map = {
        "ERA":"earnedRunAverage",
        "Strikeouts":"strikeouts",
        "Wins":"wins",
        "WHIP":"whip",
        "Saves":"saves",
        "Innings Pitched":"inningsPitched",
    }
    chosen = st.selectbox("Stat category", list(stat_map.keys()))
    top = pivot_leaders(df, stat_map[chosen])
    ascending = chosen in ["ERA","WHIP"]
    top = top.sort_values("Value", ascending=ascending).head(20)

    c1,c2,c3 = st.columns(3)
    for col, i in zip([c1,c2,c3],[0,1,2]):
        if i < len(top):
            row = top.iloc[i]
            with col:
                st.markdown(f'<div class="kpi"><div class="kpi-val">{row["Value"]}</div><div class="kpi-lbl">#{i+1} {chosen}</div><div class="kpi-sub">{row["Name"]} · {row["TeamAbb"]}</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    plot_df = top.sort_values("Value", ascending=not ascending)
    fig = px.bar(plot_df, x="Value", y="Name", orientation="h",
                 color="Value", color_continuous_scale=["#1f3a5f","#58a6ff","#cae8ff"],
                 hover_data={"Team":True})
    fig.update_layout(**PT, height=520, coloraxis_showscale=False, margin=dict(l=0,r=0,t=10,b=0))
    st.plotly_chart(fig, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TODAY'S GAMES
# ══════════════════════════════════════════════════════════════════════════════
elif "Today" in mode:
    today_str = datetime.date.today().strftime("%B %d, %Y")
    st.markdown(f"# Today's Games · {today_str}")
    with st.spinner("Fetching live scores…"):
        games = load_today_games()

    if not games:
        st.info("No games scheduled today or data unavailable.")
    else:
        live   = [g for g in games if "Progress" in g["Status"] or "In Progress" in g["Status"]]
        final  = [g for g in games if "Final" in g["Status"]]
        sched  = [g for g in games if g not in live and g not in final]

        if live:
            st.markdown('<div class="sec">🔴 Live now</div>', unsafe_allow_html=True)
            for g in live:
                st.markdown(f"""
                <div style="background:#1a2332;border:1px solid #1f6feb;border-radius:8px;padding:12px 18px;margin-bottom:8px;display:flex;justify-content:space-between;align-items:center;">
                  <div style="font-size:14px;color:#e6edf3;">{g['Away']} <span style="color:#8b949e;">vs</span> {g['Home']}</div>
                  <div style="font-family:'IBM Plex Mono',monospace;font-size:18px;color:#58a6ff;">{g['AwayScore']} – {g['HomeScore']}</div>
                  <div style="font-size:11px;color:#3fb950;">{g['Inning']}</div>
                </div>""", unsafe_allow_html=True)

        if final:
            st.markdown('<div class="sec">✅ Final</div>', unsafe_allow_html=True)
            for g in final:
                winner_side = "away" if str(g['AwayScore']) > str(g['HomeScore']) else "home"
                away_style = "color:#e6edf3;font-weight:600;" if winner_side=="away" else "color:#8b949e;"
                home_style = "color:#e6edf3;font-weight:600;" if winner_side=="home" else "color:#8b949e;"
                st.markdown(f"""
                <div style="background:#161b22;border:1px solid #21262d;border-radius:8px;padding:10px 18px;margin-bottom:6px;display:flex;justify-content:space-between;align-items:center;">
                  <div style="font-size:13px;{away_style}">{g['Away']}</div>
                  <div style="font-family:'IBM Plex Mono',monospace;font-size:16px;color:#c9d1d9;">{g['AwayScore']} – {g['HomeScore']}</div>
                  <div style="font-size:13px;{home_style}">{g['Home']}</div>
                </div>""", unsafe_allow_html=True)

        if sched:
            st.markdown('<div class="sec">📅 Upcoming</div>', unsafe_allow_html=True)
            for g in sched:
                st.markdown(f"""
                <div style="background:#161b22;border:1px solid #21262d;border-radius:8px;padding:8px 18px;margin-bottom:6px;display:flex;justify-content:space-between;align-items:center;">
                  <div style="font-size:13px;color:#c9d1d9;">{g['Away']} @ {g['Home']}</div>
                  <div style="font-size:11px;color:#8b949e;">{g['Venue']}</div>
                  <div style="font-size:11px;color:#8b949e;">{g['Status']}</div>
                </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# COMPARE PLAYERS
# ══════════════════════════════════════════════════════════════════════════════
elif "Compare" in mode:
    st.markdown(f"# Player Comparison · {SEASON}")
    comp_type = st.radio("Type", ["Batters","Pitchers"], horizontal=True)

    with st.spinner("Loading leaders…"):
        if comp_type == "Batters":
            df = load_hitting_leaders(200)
            stat_cols = {"HR":"homeRuns","AVG":"battingAverage","OPS":"onBasePlusSlugging","RBI":"rbi","SB":"stolenBases","H":"hits"}
        else:
            df = load_pitching_leaders(150)
            stat_cols = {"ERA":"earnedRunAverage","K":"strikeouts","W":"wins","WHIP":"whip","SV":"saves","IP":"inningsPitched"}

    if df.empty:
        st.error("Could not reach MLB API.")
        st.stop()

    all_players = sorted(df["Name"].unique().tolist())
    defaults = all_players[:4] if len(all_players) >= 4 else all_players
    selected = st.multiselect("Select players (2–6)", all_players, default=defaults, max_selections=6)

    if len(selected) < 2:
        st.info("Pick at least 2 players.")
        st.stop()

    player_data = {}
    for player in selected:
        player_data[player] = {}
        for short, long in stat_cols.items():
            sub = df[(df["Name"]==player) & (df["Stat"]==long)]
            if not sub.empty:
                try: player_data[player][short] = float(sub.iloc[0]["Value"])
                except: player_data[player][short] = 0.0
            else:
                player_data[player][short] = 0.0

    metrics = list(stat_cols.keys())
    fig = go.Figure()
    colors = ["#58a6ff","#3fb950","#f0883e","#d2a8ff","#ffa657","#79c0ff"]
    for i, player in enumerate(selected):
        vals = [player_data[player].get(m,0) for m in metrics]
        mx = max(vals) if max(vals) > 0 else 1
        vals_norm = [v/mx for v in vals]
        fig.add_trace(go.Scatterpolar(
            r=vals_norm + [vals_norm[0]],
            theta=metrics + [metrics[0]],
            fill="toself", name=player,
            line_color=colors[i % len(colors)],
            opacity=0.65,
            customdata=[vals + [vals[0]]],
            hovertemplate="%{theta}: %{customdata[0]:.2f}<extra>" + player + "</extra>",
        ))
    fig.update_layout(**PT, height=480,
                      polar=dict(bgcolor="#161b22",
                                 radialaxis=dict(visible=True,gridcolor="#21262d",color="#8b949e",showticklabels=False),
                                 angularaxis=dict(gridcolor="#21262d",color="#c9d1d9")),
                      showlegend=True, margin=dict(l=60,r=60,t=40,b=40))
    st.plotly_chart(fig, use_container_width=True)

    table_rows = []
    for player in selected:
        row = {"Player": player}
        row.update(player_data[player])
        table_rows.append(row)
    st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)
