import streamlit as st
import pandas as pd
import altair as alt
import sqlalchemy as sa
import os
import random
from datetime import datetime, date, timedelta
import pytz

# ---------- CONFIG ----------
st.set_page_config(
    page_title="WaterYouDoing",
    page_icon="icon.png",
    layout="centered",
    initial_sidebar_state="auto"
)
st.markdown("""
<link rel="manifest" href="manifest.json">
""", unsafe_allow_html=True)

DB_FILE = "data.db"
OLD_CSV_FILE = "data.csv"  # only used for one-time migration if it exists
DAILY_GOAL = 2000  # ml
HISTORY_DAYS = 7
TZ = pytz.timezone("Asia/Karachi")
BIRTHDAY_MONTH_DAY = (8, 1)  # Aug 1

# ---------- PERSONALIZED MESSAGE BANK ----------
# Mixed tone: sassy/teasing, never mean. Tagged by reference so it's easy to add more later.
MESSAGES = [
    # Valorant
    {"type": "Valorant", "message": "Your hydration aim is more inconsistent than your Vandal spray."},
    {"type": "Valorant", "message": "You peeked that corner dry-mouthed again. Drink water, agent."},
    {"type": "Valorant", "message": "Defuse the dehydration before the round timer hits zero."},
    {"type": "Valorant", "message": "Plant the spike, then go drink some water. Priorities."},
    # Subnautica
    {"type": "Subnautica", "message": "You explored the entire Aurora wreck but can't find a water bottle?"},
    {"type": "Subnautica", "message": "Even the Sea Emperor stays hydrated, and it lives underwater 24/7."},
    {"type": "Subnautica", "message": "Low hydration meter detected. The Reaper Leviathan is the least of your problems."},
    # HIMYM
    {"type": "HIMYM", "message": "This is the story of how you forgot to drink water, kids."},
    {"type": "HIMYM", "message": "Not legen— wait for it —dary yet. Get hydrating."},
    {"type": "HIMYM", "message": "You're the Barney of hydration — full of promises, no delivery."},
    # Brooklyn 99
    {"type": "B99", "message": "Cool cool cool cool cool, no doubt no doubt, but did you drink water? No doubt."},
    {"type": "B99", "message": "Nine-Nine! Hydration squad, where you at?"},
    {"type": "B99", "message": "Captain Holt would raise exactly one eyebrow at this hydration log."},
    # Ready Player One
    {"type": "RPO", "message": "You'd find the Copper Key faster than you'd find a water bottle."},
    {"type": "RPO", "message": "Even inside the OASIS, your real body still needs actual water."},
    # Batman
    {"type": "Batman", "message": "It's not who you are underneath, it's how hydrated you are that defines you."},
    {"type": "Batman", "message": "Gotham doesn't need a hero right now. It needs you to drink some water."},
    {"type": "Batman", "message": "Bruce Wayne has a butler for hydration reminders. You just have this app."},
    # Ben 10
    {"type": "Ben10", "message": "Even with the Omnitrix, you can't transform out of being dehydrated."},
    {"type": "Ben10", "message": "Slap that Omnitrix and turn into someone who actually drinks water."},
    # Invincible
    {"type": "Invincible", "message": "Even Viltrumites need to hydrate. Probably. Drink the water, Mark."},
    {"type": "Invincible", "message": "You're not invincible. Drink the water."},
    # General / original
    {"type": "Roast", "message": "Drink water before your organs file a complaint."},
    {"type": "Roast", "message": "Your cells are crispier than KFC."},
    {"type": "Quotes", "message": "Proud of you for hydrating (even a little)."},
    {"type": "Council", "message": "🧘ye deekho chookari maar ke aapke paani peene ka intezaar."}
]

# ---------- MEMES ----------
MEMES = [
    {"url": "https://i.imgflip.com/aaiih1.jpg", "caption": ""},
    {"url": "https://i.imgflip.com/aaiinq.jpg", "caption": ""},
    {"url": "https://i.imgflip.com/aaijhu.jpg", "caption": ""},
    {"url": "https://i.imgflip.com/aailz2.jpg", "caption": ""},
    {"url": "https://i.imgflip.com/aaim2z.jpg", "caption": ""},
    {"url": "https://i.imgflip.com/aaimit.jpg", "caption": ""},
    {"url": "https://i.imgflip.com/aaios5.jpg", "caption": ""},
    {"url": "https://i.pinimg.com/1200x/6a/dd/a7/6adda7b08880e234247df0c566b8ebc3.jpg", "caption": "kiun nhin pi rhe aap paani."},
    {"url": "https://i.pinimg.com/1200x/3e/31/7f/3e317fdabd3c015819e6e096ca030e7f.jpg", "caption": "You're not the only one with cameras."},
    {"url": "https://i.pinimg.com/1200x/b2/af/75/b2af75f216dd5cd75379789beff5b8a1.jpg", "caption": "imagine fardan living longer than you cause he drank water and you didn't."},
    {"url": "https://i.pinimg.com/736x/37/c1/4c/37c14ca7f0d61a2a8db4788c09dd336b.jpg", "caption": "me if u dont drink water."},
    {"url": "https://i.pinimg.com/736x/97/74/cd/9774cd9bd7daead2ac764adb34a0e72f.jpg", "caption": "your mom if u need to go to the doc again."},
    {"url": "https://i.imgflip.com/ab2rs7.jpg", "caption": ""},
    {"url": "https://i.imgflip.com/ab2s52.jpg", "caption": ""},
    {"url": "https://i.imgflip.com/ab2seh.jpg", "caption": ""},
    {"url": "https://i.imgflip.com/ab2sld.jpg", "caption": ""},
    {"url": "https://i.imgflip.com/ab2sup.jpg", "caption": ""},
    {"url": "https://i.imgflip.com/ab2syj.jpg", "caption": ""},
    {"url": "https://i.imgflip.com/ab2t61.jpg", "caption": ""},
    {"url": "https://i.imgflip.com/ab2thh.jpg", "caption": ""},
    {"url": "https://i.imgflip.com/ab2tqs.jpg", "caption": ""},
    {"url": "https://i.imgflip.com/ab2ttv.jpg", "caption": ""},
    {"url": "https://i.imgflip.com/ab2txr.jpg", "caption": ""}
]

# ---------- BADGES / MILESTONES ----------
# Each check receives a `stats` dict (see get_stats below).
BADGES = [
    {"id": "spike_planted", "name": "Spike Planted", "icon": "🎯",
     "desc": "Logged your first entry ever.",
     "check": lambda s: s["lifetime_entries"] >= 1},
    {"id": "first_ace", "name": "Ace", "icon": "🔫",
     "desc": "Hit your daily goal for the first time.",
     "check": lambda s: s["days_hit_goal"] >= 1},
    {"id": "omnitrix", "name": "Omnitrix Unlocked", "icon": "⏱️",
     "desc": "10 liters logged lifetime.",
     "check": lambda s: s["lifetime_ml"] >= 10_000},
    {"id": "oasis_key1", "name": "Copper Key", "icon": "🔑",
     "desc": "Reached a 7-day streak.",
     "check": lambda s: s["best_streak"] >= 7},
    {"id": "nine_nine", "name": "Nine-Nine!", "icon": "🚔",
     "desc": "99 entries logged total. Cool cool cool cool.",
     "check": lambda s: s["lifetime_entries"] >= 99},
    {"id": "oasis_key2", "name": "Jade Key", "icon": "🗝️",
     "desc": "Reached a 14-day streak.",
     "check": lambda s: s["best_streak"] >= 14},
    {"id": "lifepod", "name": "Lifepod 5 Survivor", "icon": "🌊",
     "desc": "50 liters logged lifetime.",
     "check": lambda s: s["lifetime_ml"] >= 50_000},
    {"id": "oasis_key3", "name": "Halliday's Egg", "icon": "🥚",
     "desc": "Reached a 21-day streak.",
     "check": lambda s: s["best_streak"] >= 21},
    {"id": "dark_knight", "name": "I Am the Night", "icon": "🦇",
     "desc": "Reached a 30-day streak.",
     "check": lambda s: s["best_streak"] >= 30},
    {"id": "legendary", "name": "Legen...dary", "icon": "🏆",
     "desc": "100 liters logged lifetime.",
     "check": lambda s: s["lifetime_ml"] >= 100_000},
    {"id": "viltrumite", "name": "Viltrumite Endurance", "icon": "💪",
     "desc": "Reached a 50-day streak. Practically invincible.",
     "check": lambda s: s["best_streak"] >= 50},
]

# ---------- DATABASE ----------
# Uses a hosted Postgres (e.g. Supabase) when credentials are provided via
# st.secrets["postgres"]["url"] — this survives redeploys/restarts on free hosting.
# Falls back to a local SQLite file when no secrets are set (handy for local dev/testing).

@st.cache_resource
def get_engine():
    if "postgres" in st.secrets:
        return sa.create_engine(st.secrets["postgres"]["url"], pool_pre_ping=True)
    return sa.create_engine(f"sqlite:///{DB_FILE}")


ENGINE = get_engine()
IS_POSTGRES = ENGINE.dialect.name == "postgresql"


def init_db():
    """Create the table if it doesn't exist, and migrate an old local CSV once if present."""
    with ENGINE.begin() as conn:
        if IS_POSTGRES:
            conn.execute(sa.text("""
                CREATE TABLE IF NOT EXISTS entries (
                    id SERIAL PRIMARY KEY,
                    date TEXT NOT NULL,
                    time TEXT NOT NULL,
                    amount_ml INTEGER NOT NULL
                )
            """))
        else:
            conn.execute(sa.text("""
                CREATE TABLE IF NOT EXISTS entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    time TEXT NOT NULL,
                    amount_ml INTEGER NOT NULL
                )
            """))

    if os.path.exists(OLD_CSV_FILE):
        with ENGINE.begin() as conn:
            count = conn.execute(sa.text("SELECT COUNT(*) FROM entries")).scalar()
            if count == 0:
                try:
                    old_df = pd.read_csv(OLD_CSV_FILE)
                    if {"Date", "Time", "Amount (ml)"}.issubset(old_df.columns):
                        for _, row in old_df.iterrows():
                            conn.execute(
                                sa.text("INSERT INTO entries (date, time, amount_ml) VALUES (:d, :t, :a)"),
                                {"d": str(row["Date"]), "t": str(row["Time"]), "a": int(row["Amount (ml)"])}
                            )
                    os.rename(OLD_CSV_FILE, OLD_CSV_FILE + ".migrated.bak")
                except Exception:
                    pass


def load_data():
    df = pd.read_sql("SELECT * FROM entries", ENGINE)

    if df.empty:
        return pd.DataFrame(columns=["id", "Date", "Time", "Amount (ml)"])

    df["Date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
    df["Time"] = pd.to_datetime(df["time"], errors="coerce").dt.time
    df["Time"] = df["Time"].fillna(datetime.strptime("00:00:00", "%H:%M:%S").time())
    df["Amount (ml)"] = pd.to_numeric(df["amount_ml"], errors="coerce").fillna(0).astype(int)

    return df[["id", "Date", "Time", "Amount (ml)"]]


def add_entry(amount_ml):
    now = datetime.now(TZ)
    with ENGINE.begin() as conn:
        conn.execute(
            sa.text("INSERT INTO entries (date, time, amount_ml) VALUES (:d, :t, :a)"),
            {"d": now.date().isoformat(), "t": now.time().replace(microsecond=0).isoformat(), "a": int(amount_ml)}
        )
    return now


def delete_entries(ids):
    if not ids:
        return False
    with ENGINE.begin() as conn:
        for i in ids:
            conn.execute(sa.text("DELETE FROM entries WHERE id = :i"), {"i": int(i)})
    return True


def get_daily_total(df, target_date):
    if df.empty:
        return 0
    return int(df[df["Date"] == target_date]["Amount (ml)"].sum())


def get_history_aggregated(df, days=HISTORY_DAYS):
    today = date.today()
    dates = [today - timedelta(days=i) for i in range(days - 1, -1, -1)]
    totals = [get_daily_total(df, d) for d in dates]
    return dates, totals


# ---------- STREAKS / STATS / BADGES ----------
def get_goal_days(df):
    """Set of dates where the daily goal was met."""
    if df.empty:
        return set()
    daily_totals = df.groupby("Date")["Amount (ml)"].sum()
    return set(d for d, total in daily_totals.items() if total >= DAILY_GOAL)


def get_streaks(goal_days):
    """Returns (current_streak, best_streak) in days."""
    if not goal_days:
        return 0, 0

    today = date.today()
    current = 0
    check_date = today if today in goal_days else today - timedelta(days=1)
    while check_date in goal_days:
        current += 1
        check_date -= timedelta(days=1)

    sorted_days = sorted(goal_days)
    best = 1
    run = 1
    for i in range(1, len(sorted_days)):
        if sorted_days[i] == sorted_days[i - 1] + timedelta(days=1):
            run += 1
        else:
            run = 1
        best = max(best, run)

    return current, max(best, current)


def get_stats(df):
    goal_days = get_goal_days(df)
    current_streak, best_streak = get_streaks(goal_days)
    return {
        "lifetime_ml": int(df["Amount (ml)"].sum()) if not df.empty else 0,
        "lifetime_entries": int(len(df)),
        "days_hit_goal": len(goal_days),
        "current_streak": current_streak,
        "best_streak": best_streak,
    }


def get_unlocked_badges(stats):
    return [b for b in BADGES if b["check"](stats)]


RANKS = [
    (0, "Iron"), (3, "Bronze"), (7, "Silver"), (14, "Gold"),
    (21, "Platinum"), (30, "Diamond"), (45, "Ascendant"),
    (60, "Immortal"), (90, "Radiant"),
]


def get_rank(streak_days):
    rank = RANKS[0][1]
    for threshold, name in RANKS:
        if streak_days >= threshold:
            rank = name
    return rank


def get_hud_status(total_today, goal):
    pct = total_today / goal if goal else 0
    if pct >= 1:
        return "OPTIMAL", "All systems hydrated."
    elif pct >= 0.5:
        return "STABLE", "Holding the line. Keep going."
    elif pct >= 0.2:
        return "LOW", "Hydration dropping. Resupply soon."
    else:
        return "CRITICAL", "Reaper Leviathan Approaching. Drink water now."


def get_week_avg(df, weeks_ago=0):
    """Average daily ml for a given week (0 = this week, 1 = last week), Monday-start."""
    today = date.today()
    start_this_week = today - timedelta(days=today.weekday())
    start = start_this_week - timedelta(weeks=weeks_ago)
    end_cap = min(start + timedelta(days=6), today)
    if end_cap < start:
        return 0.0
    days = [start + timedelta(days=i) for i in range((end_cap - start).days + 1)]
    totals = [get_daily_total(df, d) for d in days]
    return sum(totals) / len(totals) if totals else 0.0


def announce_entry(amount, now, data_after):
    """Shared success/meme/message block used by both quick-add and custom-add."""
    st.success(f"Added {amount} ml at {now.strftime('%I:%M %p')}")

    total_today = get_daily_total(data_after, date.today())
    if total_today >= DAILY_GOAL:
        st.success("🎉 ACE! You hit today's goal!")

    meme = random.choice(MEMES)
    st.image(meme["url"], use_container_width=True)

    msg = random.choice(MESSAGES)
    st.markdown(f"<div class='custom-box'>{msg['message']}</div>", unsafe_allow_html=True)


# ---------- SESSION ----------
if "refresh" not in st.session_state:
    st.session_state.refresh = 0

# ---------- THEME: red / black / jasmine ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@500;600;700&family=Cormorant+Garamond:ital@1&family=Saira+Condensed:wght@700;800&display=swap');

:root {
    --jw-red: #B3001B;
    --jw-red-bright: #FF4655;
    --jw-black: #0D0D0D;
    --jw-panel: #181818;
    --jw-jasmine: #FFF6E0;
}

html, body, [class*="css"] {
    font-family: 'Rajdhani', sans-serif !important;
}

[data-testid="stAppViewContainer"] {
    background-color: var(--jw-black);
    background-image:
        radial-gradient(circle at 15% 20%, rgba(179,0,27,0.10) 0%, transparent 40%),
        radial-gradient(circle at 85% 80%, rgba(179,0,27,0.08) 0%, transparent 45%),
        repeating-linear-gradient(135deg, rgba(255,255,255,0.015) 0px, rgba(255,255,255,0.015) 2px, transparent 2px, transparent 14px);
}
[data-testid="stHeader"] {
    background-color: rgba(0,0,0,0);
}

h1, h2, h3, h4 {
    color: var(--jw-jasmine) !important;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    font-weight: 700 !important;
}
.stMarkdown p, label, span {
    color: var(--jw-jasmine) !important;
}

div.stButton > button {
    min-width: 90px;
    padding: 8px 4px;
    font-size: 15px;
    margin: 2px 0px;
    background-color: var(--jw-red);
    color: var(--jw-jasmine);
    border: 1px solid var(--jw-red-bright);
    border-radius: 6px;
    font-weight: 700;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    box-shadow: 0 3px 0 rgba(0,0,0,0.5);
    transition: transform 0.12s ease, box-shadow 0.12s ease, background-color 0.12s ease;
}
div.stButton > button:hover {
    background-color: var(--jw-red-bright);
    color: var(--jw-black);
    border: 1px solid var(--jw-jasmine);
    transform: translateY(-2px);
    box-shadow: 0 5px 0 rgba(0,0,0,0.5);
}
div.stButton > button:active {
    transform: translateY(1px);
    box-shadow: 0 1px 0 rgba(0,0,0,0.5);
}

.custom-box {
    background-color: var(--jw-panel);
    color: var(--jw-jasmine);
    padding: 10px 14px;
    border-radius: 8px;
    margin-top: 8px;
    border-left: 4px solid var(--jw-red-bright);
    box-shadow: 0 4px 10px rgba(0,0,0,0.4);
    font-family: 'Cormorant Garamond', serif;
    font-style: italic;
    font-size: 16px;
}

.streak-box {
    background: linear-gradient(135deg, var(--jw-red) 0%, var(--jw-black) 100%);
    color: var(--jw-jasmine);
    padding: 14px 18px;
    border-radius: 10px;
    border: 1px solid var(--jw-red-bright);
    margin-bottom: 10px;
    box-shadow: 0 6px 16px rgba(179,0,27,0.35);
}
.streak-box .big {
    font-size: 28px;
    font-weight: 700;
}

.rank-tag {
    display: inline-block;
    background-color: var(--jw-black);
    color: var(--jw-red-bright);
    border: 1px solid var(--jw-red-bright);
    border-radius: 4px;
    padding: 2px 10px;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-left: 4px;
}

.app-title {
    font-family: 'Saira Condensed', sans-serif;
    font-weight: 800;
    font-size: 44px;
    text-transform: uppercase;
    letter-spacing: 2px;
    color: var(--jw-jasmine);
    text-shadow: 0 0 14px rgba(255,70,85,0.55), 2px 2px 0 rgba(0,0,0,0.5);
    transform: skewX(-6deg);
    display: inline-block;
    line-height: 1;
}
.app-title-wrap {
    position: relative;
    padding-bottom: 6px;
}
.app-title-underline {
    height: 4px;
    width: 220px;
    background: linear-gradient(90deg, var(--jw-red-bright), transparent);
    margin-top: 2px;
}

.hud-banner {
    border-radius: 8px;
    padding: 10px 16px;
    margin: 10px 0 16px 0;
    font-weight: 700;
    letter-spacing: 0.5px;
    box-shadow: 0 4px 10px rgba(0,0,0,0.4);
    border: 1px solid;
}

.badge-locked {
    opacity: 0.35;
    filter: grayscale(1);
}
.badge-card {
    background-color: var(--jw-panel);
    border: 1px solid var(--jw-red);
    border-radius: 8px;
    padding: 10px;
    text-align: center;
    margin-bottom: 6px;
    box-shadow: 0 4px 10px rgba(0,0,0,0.35);
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.badge-card:hover {
    transform: translateY(-3px) scale(1.03);
    box-shadow: 0 8px 18px rgba(255,70,85,0.25);
}
.badge-card .icon {
    font-size: 26px;
}
.badge-card .name {
    color: var(--jw-jasmine);
    font-size: 13px;
    font-weight: 700;
}
.badge-card .desc {
    color: #c9c0a8;
    font-size: 11px;
    font-family: 'Cormorant Garamond', serif;
    font-style: italic;
}

[data-testid="stProgress"] > div > div {
    background-color: var(--jw-red-bright) !important;
}

hr {
    border-color: rgba(255,70,85,0.25) !important;
    margin: 0.5rem 0 !important;
}

/* tighten default Streamlit spacing so more fits without scrolling */
.block-container {
    padding-top: 2rem !important;
    padding-bottom: 2rem !important;
}
[data-testid="stVerticalBlock"] {
    gap: 0.6rem !important;
}
</style>
""", unsafe_allow_html=True)

# ---------- UI ----------
# Init + load
init_db()
data = load_data()
stats = get_stats(data)
current_rank = get_rank(stats["current_streak"])

st.markdown(f"""
<div class="app-title-wrap">
  <div style="display:flex; align-items:center; gap:14px;">
    <div class="app-title">WaterYouDoing</div>
    <span class="rank-tag">{current_rank}</span>
  </div>
  <div class="app-title-underline"></div>
</div>
""", unsafe_allow_html=True)

# Birthday easter egg
today_now = date.today()
if (today_now.month, today_now.day) == BIRTHDAY_MONTH_DAY:
    st.balloons()
    st.markdown(
        "<div class='custom-box'>🌺 Happy Birthday! Even Viltrumites take a hydration break today. "
        "Drink water, then go enjoy your day. 🎂</div>",
        unsafe_allow_html=True
    )

st.caption(f"Daily goal: **{DAILY_GOAL} ml**")

# HUD status banner — reflects today's hydration before any column split
_today_total_for_hud = get_daily_total(data, date.today())
_label, _subtext = get_hud_status(_today_total_for_hud, DAILY_GOAL)
_hud_colors = {
    "OPTIMAL": ("#1f4d2b", "#3ddc6f"),
    "STABLE": ("#4d4319", "#ffd23d"),
    "LOW": ("#4d2c12", "#ff9d3d"),
    "CRITICAL": ("#4d1119", "#ff4655"),
}
_bg, _border = _hud_colors[_label]
st.markdown(f"""
<div class="hud-banner" style="background-color:{_bg}; border-color:{_border}; color:{_border};">
    STATUS: {_label} — {_subtext}
</div>
""", unsafe_allow_html=True)

# Streak banner
streak_cols = st.columns(2)
with streak_cols[0]:
    st.markdown(f"""
    <div class="streak-box">
        Current Streak<br><span class="big">{stats['current_streak']} day{'s' if stats['current_streak'] != 1 else ''}</span>
    </div>
    """, unsafe_allow_html=True)
with streak_cols[1]:
    st.markdown(f"""
    <div class="streak-box">
        Best Streak<br><span class="big">{stats['best_streak']} day{'s' if stats['best_streak'] != 1 else ''}</span>
    </div>
    """, unsafe_allow_html=True)

# view_date is needed below, so define it before the column split
view_date = st.date_input("View date", value=date.today())

# Layout — only put genuinely similar-sized content side by side.
# Everything longer (table, chart, briefings) goes full-width below so one
# column never ends up much taller than the other with a void beside it.
col1, col2 = st.columns(2)

# ---------- LEFT COLUMN: quick add ----------
with col1:
    st.subheader("Buy Phase — Stock Up")

    quick_amounts = [250, 500]
    quick_cols = st.columns(len(quick_amounts))
    for idx, amt in enumerate(quick_amounts):
        with quick_cols[idx]:
            if st.button(f"+{amt} ml", key=f"quick_{amt}"):
                now = add_entry(amt)
                data = load_data()
                stats = get_stats(data)
                announce_entry(amt, now, data)
                st.session_state.refresh += 1

    custom_amount = st.number_input("Or type amount (ml)", min_value=0, step=50, value=250)
    if st.button("Add entry"):
        if custom_amount <= 0:
            st.warning("Stop trying stupid things, lil bro")
        else:
            now = add_entry(custom_amount)
            data = load_data()
            stats = get_stats(data)
            announce_entry(custom_amount, now, data)
            st.session_state.refresh += 1

# ---------- RIGHT COLUMN: today's status ----------
with col2:
    st.subheader("Mission Status")

    total_today = get_daily_total(data, view_date)
    st.write(f"Total for {view_date.isoformat()}: **{total_today} ml**")

    progress_val = min(total_today / DAILY_GOAL, 1)
    st.progress(progress_val)
    st.write(f"{int(progress_val * 100)}% of {DAILY_GOAL} ml")

# ---------- FULL-WIDTH: Match History ----------
st.markdown("---")
st.subheader(f"Match History — {view_date.isoformat()}")
data = load_data()
view_df = data[data["Date"] == view_date].copy()

if not view_df.empty:
    view_df_display = view_df.copy()
    view_df_display["Time"] = view_df_display["Time"].apply(
        lambda t: datetime.strptime(str(t), "%H:%M:%S").strftime("%I:%M %p")
    )

    st.dataframe(
        view_df_display[["id", "Time", "Amount (ml)"]].rename(columns={"id": "ID"}),
        use_container_width=True,
        hide_index=True
    )

    to_delete = st.multiselect("Select rows to delete (ID)", view_df_display["id"])

    if st.button("Delete selected"):
        if to_delete:
            delete_entries(to_delete)
            st.success("Deleted selected entries.")
            st.session_state.refresh += 1
        else:
            st.warning("Pick at least one row to delete.")
else:
    st.write("No entries for this date yet. Add one above!")

# ---------- FULL-WIDTH: 7-day chart ----------
st.markdown("---")
dates, totals = get_history_aggregated(data)
chart_df = pd.DataFrame({"date": [d.isoformat() for d in dates], "total": totals})
st.write("7-day intake log:")

y_max = max(DAILY_GOAL, int(chart_df["total"].max()) if not chart_df.empty else 0)
water_chart = (
    alt.Chart(chart_df)
    .mark_bar(color="#FF4655", cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
    .encode(
        x=alt.X("date:N", sort=None, title=None, axis=alt.Axis(labelColor="#FFF6E0", labelAngle=-45)),
        y=alt.Y(
            "total:Q",
            title="ml",
            scale=alt.Scale(domain=[0, y_max]),
            axis=alt.Axis(labelColor="#FFF6E0", titleColor="#FFF6E0"),
        ),
    )
    .properties(height=300, padding={"left": 55, "right": 15, "top": 10, "bottom": 10})
    .configure_view(strokeWidth=0)
    .configure_axis(grid=True, gridColor="#2a2a2a")
)
st.altair_chart(water_chart, use_container_width=True)

# ---------- Intel Briefing + Captain Holt's Briefing, side by side ----------
st.markdown("---")
intel_col, holt_col = st.columns(2)

with intel_col:
    st.subheader("Intel Briefing — Week vs Week")
    this_week = get_week_avg(data, 0)
    last_week = get_week_avg(data, 1)
    if last_week > 0:
        pct_change = ((this_week - last_week) / last_week) * 100
        direction = "up" if pct_change >= 0 else "down"
        st.markdown(
            f"<div class='custom-box'>This week's avg: <b>{this_week:.0f} ml/day</b><br>"
            f"Last week's avg: <b>{last_week:.0f} ml/day</b><br>"
            f"That's <b>{abs(pct_change):.0f}% {direction}</b> from last week.</div>",
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"<div class='custom-box'>This week's avg: <b>{this_week:.0f} ml/day</b><br>"
            f"Not enough history yet for a week-over-week comparison.</div>",
            unsafe_allow_html=True
        )

with holt_col:
    st.subheader("Captain Holt's Briefing")
    st.write("Your drinking habits are not up to the mark.")

    meme = random.choice(MEMES)
    st.markdown(
        f"<img src='{meme['url']}' style='width:100%; max-height:220px; object-fit:cover; "
        f"border-radius:8px; border:1px solid var(--jw-red);' />",
        unsafe_allow_html=True
    )
    msg = random.choice(MESSAGES)
    st.markdown(f"<div class='custom-box'>{msg['message']}</div>", unsafe_allow_html=True)

# ---------- BADGES ----------
st.markdown("---")
st.subheader("Loadout Unlocks")
unlocked = get_unlocked_badges(stats)
unlocked_ids = {b["id"] for b in unlocked}
st.write(f"Unlocked: **{len(unlocked)} / {len(BADGES)}**")

badge_cols = st.columns(4)
for idx, badge in enumerate(BADGES):
    is_unlocked = badge["id"] in unlocked_ids
    css_class = "badge-card" if is_unlocked else "badge-card badge-locked"
    icon = badge["icon"] if is_unlocked else "🔒"
    with badge_cols[idx % 4]:
        st.markdown(f"""
        <div class="{css_class}">
            <div class="icon">{icon}</div>
            <div class="name">{badge['name']}</div>
            <div class="desc">{badge['desc']}</div>
        </div>
        """, unsafe_allow_html=True)

# Raw data toggle
st.markdown("---")
if st.checkbox("Show raw data (DB)"):
    st.dataframe(load_data(), use_container_width=True)
