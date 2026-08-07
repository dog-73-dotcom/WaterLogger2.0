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
    page_title="HydrAgent",
    page_icon="icon.png",
    layout="centered",
    initial_sidebar_state="auto"
)
st.markdown("""
<link rel="manifest" href="manifest.json">
""", unsafe_allow_html=True)

DB_FILE = "data.db"
OLD_CSV_FILE = "data.csv"
DAILY_GOAL = 2000  # ml
HISTORY_DAYS = 7
TZ = pytz.timezone("Asia/Muscat")  # Oman (UTC+4)
BIRTHDAY_MONTH_DAY = (8, 1)  # Aug 1

# ---------- ANNIVERSARY DATES ----------
# (month, day, year_or_None, label, message)
ANNIVERSARIES = [
    (2, 17, 2024, "Reunion",
     "Today marks {years} year{s} since the reunion. Still not drinking enough water though. Some things never change."),
    (6, 20, 2026, "The Confession",
     "One year of courage. Still takes more guts to hit 2000ml a day apparently."),
    (9, 15, 2025, "The ILY",
     "Said it {years} year{s} ago. The app remembers even if you pretend not to. Drink water."),
    (BIRTHDAY_MONTH_DAY[0], BIRTHDAY_MONTH_DAY[1], 2007, "Birthday",
     "Another year older. Another year of questionable hydration decisions. Happy birthday. 🎂"),
]

# ---------- ROAST ESCALATION BY TIME SINCE LAST ENTRY ----------
# (hours_since_last, roast_messages)
ESCALATION_TIERS = [
    (0, 2, [
        "Logged recently. Impressive. Don't get comfortable.",
        "Look at you, barely keeping it together. Still counts though.",
        "Hydration status: marginally acceptable. Don't push it.",
    ]),
    (2, 4, [
        "It's been a while. Your cells are starting to file paperwork.",
        "Two hours without water? Even the Sea Emperor is disappointed.",
        "Cool cool cool cool. No water. No doubt no doubt.",
    ]),
    (4, 6, [
        "FOUR HOURS. The Omnitrix could fix this. Sadly, you don't have one.",
        "Gotham is literally collapsing and you still haven't had water.",
        "At this point Fardan is winning. Think about that.",
    ]),
    (6, 999, [
        "SIX HOURS. The Reaper Leviathan has been notified of your location.",
        "This is not a drill. CRITICAL HYDRATION FAILURE. Even Viltrumites drink water.",
        "Six hours without water. Batman would be ashamed. Actually ashamed.",
        "Mark Grayson survives being punched through mountains. You can't survive drinking water. Incredible.",
    ]),
]

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
    """Create tables if they don't exist, add user_id column if missing."""
    with ENGINE.begin() as conn:
        if IS_POSTGRES:
            conn.execute(sa.text("""
                CREATE TABLE IF NOT EXISTS entries (
                    id SERIAL PRIMARY KEY,
                    date TEXT NOT NULL,
                    time TEXT NOT NULL,
                    amount_ml INTEGER NOT NULL,
                    user_id TEXT NOT NULL DEFAULT '1'
                )
            """))
            conn.execute(sa.text("""
                CREATE TABLE IF NOT EXISTS moods (
                    id SERIAL PRIMARY KEY,
                    date TEXT NOT NULL,
                    mood_score INTEGER NOT NULL,
                    mood_label TEXT NOT NULL,
                    note TEXT,
                    user_id TEXT NOT NULL DEFAULT '1',
                    UNIQUE(date, user_id)
                )
            """))
            conn.execute(sa.text("""
                CREATE TABLE IF NOT EXISTS admin_messages (
                    id SERIAL PRIMARY KEY,
                    deliver_date TEXT NOT NULL,
                    message TEXT NOT NULL,
                    delivered INTEGER NOT NULL DEFAULT 0
                )
            """))
            # Safely add user_id to existing tables if missing
            for tbl in ["entries", "moods"]:
                try:
                    conn.execute(sa.text(f"ALTER TABLE {tbl} ADD COLUMN user_id TEXT NOT NULL DEFAULT '1'"))
                except Exception:
                    pass  # column already exists
        else:
            conn.execute(sa.text("""
                CREATE TABLE IF NOT EXISTS entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    time TEXT NOT NULL,
                    amount_ml INTEGER NOT NULL,
                    user_id TEXT NOT NULL DEFAULT '1'
                )
            """))
            conn.execute(sa.text("""
                CREATE TABLE IF NOT EXISTS moods (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    mood_score INTEGER NOT NULL,
                    mood_label TEXT NOT NULL,
                    note TEXT,
                    user_id TEXT NOT NULL DEFAULT '1',
                    UNIQUE(date, user_id)
                )
            """))
            conn.execute(sa.text("""
                CREATE TABLE IF NOT EXISTS admin_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    deliver_date TEXT NOT NULL,
                    message TEXT NOT NULL,
                    delivered INTEGER NOT NULL DEFAULT 0
                )
            """))
            for tbl in ["entries", "moods"]:
                try:
                    conn.execute(sa.text(f"ALTER TABLE {tbl} ADD COLUMN user_id TEXT NOT NULL DEFAULT '1'"))
                except Exception:
                    pass

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


def load_data(user_id="1"):
    try:
        with ENGINE.connect() as conn:
            result = conn.execute(sa.text(
                "SELECT * FROM entries WHERE user_id = :uid"
            ), {"uid": user_id})
            rows = result.fetchall()
            cols = result.keys()
        if not rows:
            return pd.DataFrame(columns=["id", "Date", "Time", "Amount (ml)"])
        df = pd.DataFrame(rows, columns=list(cols))
    except Exception:
        return pd.DataFrame(columns=["id", "Date", "Time", "Amount (ml)"])
    df["Date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
    df["Time"] = pd.to_datetime(df["time"], errors="coerce").dt.time
    df["Time"] = df["Time"].fillna(datetime.strptime("00:00:00", "%H:%M:%S").time())
    df["Amount (ml)"] = pd.to_numeric(df["amount_ml"], errors="coerce").fillna(0).astype(int)
    return df[["id", "Date", "Time", "Amount (ml)"]]


def add_entry(amount_ml, user_id="1"):
    now = datetime.now(TZ)
    with ENGINE.begin() as conn:
        conn.execute(
            sa.text("INSERT INTO entries (date, time, amount_ml, user_id) VALUES (:d, :t, :a, :uid)"),
            {"d": now.date().isoformat(), "t": now.time().replace(microsecond=0).isoformat(),
             "a": int(amount_ml), "uid": user_id}
        )
    return now


def delete_entries(ids, user_id="1"):
    if not ids:
        return False
    with ENGINE.begin() as conn:
        for i in ids:
            conn.execute(sa.text(
                "DELETE FROM entries WHERE id = :i AND user_id = :uid"
            ), {"i": int(i), "uid": user_id})
    return True


# ---------- MOOD ----------
MOOD_OPTIONS = {
    "10 — Radiant: on top of the world": 10,
    "9 — Ascendant: genuinely great": 9,
    "8 — Really good": 8,
    "7 — Good": 7,
    "6 — Pretty okay": 6,
    "5 — Meh": 5,
    "4 — Not great": 4,
    "3 — Bad": 3,
    "2 — Awful": 2,
    "1 — Deceased: do not disturb": 1,
}
MOOD_COLORS = {
    10: "#3ddc6f", 9: "#5ee87a", 8: "#a8e06a", 7: "#c8e86a",
    6: "#ffd23d", 5: "#ffc03d", 4: "#ff9d3d", 3: "#ff7a3d",
    2: "#ff5533", 1: "#ff4655"
}


def save_mood(target_date, mood_label, note="", user_id="1"):
    score = MOOD_OPTIONS[mood_label]
    with ENGINE.begin() as conn:
        if IS_POSTGRES:
            conn.execute(sa.text("""
                INSERT INTO moods (date, mood_score, mood_label, note, user_id)
                VALUES (:d, :s, :l, :n, :uid)
                ON CONFLICT (date, user_id) DO UPDATE SET mood_score=:s, mood_label=:l, note=:n
            """), {"d": str(target_date), "s": score, "l": mood_label, "n": note, "uid": user_id})
        else:
            conn.execute(sa.text("""
                INSERT INTO moods (date, mood_score, mood_label, note, user_id)
                VALUES (:d, :s, :l, :n, :uid)
                ON CONFLICT(date, user_id) DO UPDATE SET mood_score=:s, mood_label=:l, note=:n
            """), {"d": str(target_date), "s": score, "l": mood_label, "n": note, "uid": user_id})


def load_moods(user_id="1"):
    try:
        with ENGINE.connect() as conn:
            result = conn.execute(sa.text(
                "SELECT * FROM moods WHERE user_id = :uid ORDER BY date DESC"
            ), {"uid": user_id})
            rows = result.fetchall()
            cols = result.keys()
        if not rows:
            return pd.DataFrame(columns=["id", "date", "mood_score", "mood_label", "note"])
        df = pd.DataFrame(rows, columns=list(cols))
        df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
        return df
    except Exception:
        return pd.DataFrame(columns=["id", "date", "mood_score", "mood_label", "note"])


def get_mood_for_date(mood_df, target_date):
    row = mood_df[mood_df["date"] == target_date]
    if row.empty:
        return None, None, None
    r = row.iloc[0]
    return int(r["mood_score"]), r["mood_label"], r["note"]


def get_monthly_mood(mood_df, year, month):
    if mood_df.empty:
        return pd.DataFrame()
    mask = mood_df["date"].apply(lambda d: d.year == year and d.month == month)
    return mood_df[mask].copy()


def get_weekly_best_worst(df):
    """Returns best and worst day-of-week label by average daily water intake."""
    if df.empty:
        return None, None
    df = df.copy()
    df["dow"] = df["Date"].apply(lambda d: d.strftime("%A"))
    avg = df.groupby("dow")["Amount (ml)"].sum() / df.groupby("dow")["Date"].nunique()
    if len(avg) < 2:
        return None, None
    return avg.idxmax(), avg.idxmin()


def get_anniversary_message(today):
    """Return a message if today matches any anniversary, else None."""
    messages = []
    for month, day, year, label, template in ANNIVERSARIES:
        if today.month == month and today.day == day:
            years = today.year - year if year else 1
            s = "s" if years != 1 else ""
            # For same-year events (years == 0), still show the message but say "today"
            if years == 0:
                msg = template.format(years="less than a", s="")
            else:
                msg = template.format(years=years, s=s)
            messages.append((label, msg))
    return messages


def get_escalation_message(df_today):
    """Return a roast based on how long since the last water entry today."""
    if df_today.empty:
        return ESCALATION_TIERS[-1][2][-1]

    now = datetime.now(TZ)
    last_time = df_today["Time"].max()
    if last_time is None or str(last_time) == "NaT":
        return ESCALATION_TIERS[-1][2][-1]

    try:
        last_dt = TZ.localize(datetime.combine(date.today(), last_time))
        hours_since = (now - last_dt).total_seconds() / 3600
    except Exception:
        return ESCALATION_TIERS[0][2][0]

    for low, high, msgs in ESCALATION_TIERS:
        if low <= hours_since < high:
            return random.choice(msgs)
    return random.choice(ESCALATION_TIERS[-1][2])


def get_report_card(df, mood_df, year, month):
    """Generate a monthly report card dict."""
    import calendar
    _, days_in_month = calendar.monthrange(year, month)
    month_dates = [date(year, month, d) for d in range(1, days_in_month + 1)]
    today = date.today()
    elapsed_dates = [d for d in month_dates if d <= today]

    if not elapsed_dates:
        return None

    # Water stats
    totals = [get_daily_total(df, d) for d in elapsed_dates]
    avg_water = sum(totals) / len(totals)
    days_hit = sum(1 for t in totals if t >= DAILY_GOAL)
    hit_rate = days_hit / len(elapsed_dates)

    # Mood stats
    mood_scores = []
    if not mood_df.empty:
        for d in elapsed_dates:
            row = mood_df[mood_df["date"] == d]
            if not row.empty:
                mood_scores.append(int(row.iloc[0]["mood_score"]))
    avg_mood = sum(mood_scores) / len(mood_scores) if mood_scores else None

    # Grade: weighted 60% hit rate, 40% avg water proportion
    water_score = min(avg_water / DAILY_GOAL, 1.0)
    combined = (hit_rate * 0.6) + (water_score * 0.4)
    if combined >= 0.9:
        grade, verdict = "S", "Absolutely unstoppable. Radiant energy."
    elif combined >= 0.75:
        grade, verdict = "A", "Solid work. Viltrumite approved."
    elif combined >= 0.6:
        grade, verdict = "B", "Holding the line. Not bad, not great."
    elif combined >= 0.45:
        grade, verdict = "C", "Could be worse. Could very easily be better."
    elif combined >= 0.3:
        grade, verdict = "D", "Yikes. Fardan is somewhere out there thriving."
    else:
        grade, verdict = "F", "The Reaper Leviathan has already filed the paperwork."

    return {
        "grade": grade,
        "verdict": verdict,
        "avg_water": avg_water,
        "days_hit": days_hit,
        "total_days": len(elapsed_dates),
        "hit_rate": hit_rate,
        "avg_mood": avg_mood,
    }


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
    current_streak, best_streak, grace_yesterday = get_grace_status(df)
    return {
        "lifetime_ml": int(df["Amount (ml)"].sum()) if not df.empty else 0,
        "lifetime_entries": int(len(df)),
        "days_hit_goal": len(goal_days),
        "current_streak": current_streak,
        "best_streak": best_streak,
        "grace_yesterday": grace_yesterday,
    }


def get_unlocked_badges(stats):
    return [b for b in BADGES if b["check"](stats)]


# ---------- ADMIN MESSAGES ----------
ADMIN_PASSWORD = "hydrAgent2025"  # change this before gifting

# ---------- USERS ----------
# Names and PINs — PINs stored here for simplicity, change before going live
USERS = {
    "1": {"name": "Hana",   "pin": "1234", "color": "#FF4655"},
    "2": {"name": "Farhan", "pin": "5678", "color": "#4FC3F7"},
}

def save_admin_message(deliver_date, message):
    with ENGINE.begin() as conn:
        conn.execute(sa.text(
            "INSERT INTO admin_messages (deliver_date, message, delivered) VALUES (:d, :m, 0)"
        ), {"d": str(deliver_date), "m": message})


def get_unlocked_admin_messages():
    """Return messages whose deliver_date has arrived and haven't expired (within 5 days)."""
    today = date.today()
    cutoff = str(today - timedelta(days=5))
    today_str = str(today)
    try:
        with ENGINE.connect() as conn:
            result = conn.execute(sa.text(
                "SELECT * FROM admin_messages WHERE deliver_date <= :t AND deliver_date >= :c ORDER BY deliver_date ASC"
            ), {"t": today_str, "c": cutoff})
            rows = result.fetchall()
            cols = result.keys()
        if not rows:
            return pd.DataFrame()
        return pd.DataFrame(rows, columns=list(cols))
    except Exception:
        return pd.DataFrame()


def get_all_admin_messages():
    try:
        with ENGINE.connect() as conn:
            result = conn.execute(sa.text(
                "SELECT * FROM admin_messages ORDER BY deliver_date DESC"
            ))
            rows = result.fetchall()
            cols = result.keys()
        if not rows:
            return pd.DataFrame()
        return pd.DataFrame(rows, columns=list(cols))
    except Exception:
        return pd.DataFrame()


# ---------- GRACE PERIOD ----------
GRACE_ML = 200  # within this much of goal counts as "close call"

def get_grace_status(df):
    """
    Returns (streak, best_streak, grace_yesterday) where grace_yesterday is True
    if yesterday missed goal by <= GRACE_ML (streak is preserved but warned).
    """
    yesterday = date.today() - timedelta(days=1)
    yesterday_total = get_daily_total(df, yesterday)
    grace_yesterday = (
        yesterday_total > 0 and
        (DAILY_GOAL - GRACE_ML) <= yesterday_total < DAILY_GOAL
    )

    # Build goal_days including yesterday if in grace period
    goal_days = get_goal_days(df)
    effective_goal_days = set(goal_days)
    if grace_yesterday:
        effective_goal_days.add(yesterday)

    current, best = get_streaks(effective_goal_days)
    return current, best, grace_yesterday


# ---------- HYDRATION FORECAST ----------
def get_hydration_forecast(df_today, daily_goal):
    """
    Based on entries so far today, estimate total by midnight.
    Returns (forecast_ml, on_track, hours_remaining).
    """
    now = datetime.now(TZ)
    hours_elapsed = now.hour + now.minute / 60
    hours_remaining = max(0, 24 - hours_elapsed)

    if df_today.empty or hours_elapsed < 0.5:
        return None, None, hours_remaining

    total_so_far = int(df_today["Amount (ml)"].sum()) if "Amount (ml)" in df_today.columns else 0
    if total_so_far == 0 or hours_elapsed == 0:
        return None, None, hours_remaining

    rate_per_hour = total_so_far / hours_elapsed
    forecast = int(total_so_far + rate_per_hour * hours_remaining)
    on_track = forecast >= daily_goal
    return forecast, on_track, hours_remaining


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
if "user_id" not in st.session_state:
    st.session_state.user_id = None

# ---------- LOGIN SCREEN ----------
# Shows before anything else until a user authenticates
if st.session_state.user_id is None:
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Saira+Condensed:wght@800&family=Rajdhani:wght@600&display=swap');
    [data-testid="stAppViewContainer"] { background:#0A0A0A; }
    [data-testid="stHeader"] { background:transparent; }
    .login-title {
        font-family:'Saira Condensed',sans-serif; font-size:52px; font-weight:800;
        text-transform:uppercase; letter-spacing:3px; color:#FFF6E0;
        text-shadow:0 0 20px rgba(255,70,85,0.5); transform:skewX(-5deg);
        display:inline-block; margin-bottom:4px;
    }
    .login-sub { font-family:'Rajdhani',sans-serif; color:#8A8070; font-size:14px; letter-spacing:2px; text-transform:uppercase; margin-bottom:32px; }
    .login-underline { height:3px; width:260px; background:linear-gradient(90deg,#FF4655,transparent); margin-bottom:28px; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="login-title">HydrAgent</div>', unsafe_allow_html=True)
    st.markdown('<div class="login-underline"></div>', unsafe_allow_html=True)
    st.markdown('<div class="login-sub">Identify yourself, Agent.</div>', unsafe_allow_html=True)

    for uid, udata in USERS.items():
        with st.expander(f"I'm {udata['name']}"):
            pin_input = st.text_input("PIN", type="password", key=f"pin_{uid}", placeholder="Enter your PIN")
            if st.button(f"Enter as {udata['name']}", key=f"login_{uid}"):
                if pin_input == udata["pin"]:
                    st.session_state.user_id = uid
                    st.rerun()
                else:
                    st.error("Wrong PIN.")
    st.stop()

# User is logged in — get their info
_uid = st.session_state.user_id
_uname = USERS[_uid]["name"]
_ucolor = USERS[_uid]["color"]

# ---------- THEME: HydrAgent ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@500;600;700&family=Cormorant+Garamond:ital@1&family=Saira+Condensed:wght@700;800&display=swap');

:root {
    --red:      #B3001B;
    --red-b:    #FF4655;
    --black:    #0A0A0A;
    --panel:    #141414;
    --panel2:   #1C1C1C;
    --jasmine:  #FFF6E0;
    --muted:    #8A8070;
    --border:   rgba(255,70,85,0.22);
}

/* ── base ── */
html, body, [class*="css"] { font-family: 'Rajdhani', sans-serif !important; }

[data-testid="stAppViewContainer"] {
    background-color: var(--black);
    background-image:
        radial-gradient(ellipse at 10% 0%,   rgba(179,0,27,0.13) 0%, transparent 45%),
        radial-gradient(ellipse at 90% 100%, rgba(179,0,27,0.09) 0%, transparent 45%);
}
/* scanline overlay */
[data-testid="stAppViewContainer"]::after {
    content: "";
    pointer-events: none;
    position: fixed;
    inset: 0;
    background: repeating-linear-gradient(
        0deg,
        rgba(0,0,0,0.07) 0px,
        rgba(0,0,0,0.07) 1px,
        transparent 1px,
        transparent 3px
    );
    z-index: 9999;
}
[data-testid="stHeader"] { background: transparent; }

/* ── typography ── */
h1, h2, h3, h4 {
    color: var(--jasmine) !important;
    letter-spacing: 1px;
    text-transform: uppercase;
    font-weight: 700 !important;
    font-size: 1rem !important;
}
h2 { font-size: 0.85rem !important; color: var(--muted) !important; }
.stMarkdown p { color: var(--jasmine) !important; }
label, .stCaption p { color: var(--muted) !important; font-size: 12px !important; }

/* ── section cards ── */
.section-card {
    background: var(--panel);
    border: 1px solid var(--border);
    border-top: 2px solid var(--red-b);
    border-radius: 10px;
    padding: 16px 18px;
    margin-bottom: 12px;
    box-shadow: 0 6px 24px rgba(0,0,0,0.5);
}
.section-card-label {
    font-family: 'Rajdhani', sans-serif;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: var(--red-b);
    margin-bottom: 10px;
}

/* ── custom divider ── */
.divider {
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 18px 0 14px 0;
    opacity: 0.5;
}
.divider::before, .divider::after {
    content: "";
    flex: 1;
    height: 1px;
    background: var(--red-b);
}
.divider-diamond {
    width: 7px; height: 7px;
    background: var(--red-b);
    transform: rotate(45deg);
    flex-shrink: 0;
}

/* ── buttons ── */
div.stButton > button {
    min-width: 90px;
    padding: 8px 12px;
    font-size: 14px;
    font-family: 'Rajdhani', sans-serif;
    background: var(--red);
    color: var(--jasmine);
    border: 1px solid var(--red-b);
    border-radius: 5px;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
    box-shadow: 0 3px 0 rgba(0,0,0,0.6), inset 0 1px 0 rgba(255,255,255,0.06);
    transition: all 0.1s ease;
}
div.stButton > button:hover {
    background: var(--red-b);
    color: var(--black);
    transform: translateY(-2px);
    box-shadow: 0 5px 0 rgba(0,0,0,0.6), 0 0 12px rgba(255,70,85,0.35);
}
div.stButton > button:active {
    transform: translateY(1px);
    box-shadow: 0 1px 0 rgba(0,0,0,0.6);
}

/* ── inputs ── */
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
[data-testid="stDateInput"] input {
    background: var(--panel2) !important;
    border: 1px solid rgba(255,70,85,0.35) !important;
    border-radius: 5px !important;
    color: var(--jasmine) !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 15px !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stNumberInput"] input:focus {
    border-color: var(--red-b) !important;
    box-shadow: 0 0 0 2px rgba(255,70,85,0.18) !important;
}
[data-baseweb="select"] > div,
[data-baseweb="select"] > div:focus-within {
    background: var(--panel2) !important;
    border: 1px solid rgba(255,70,85,0.35) !important;
    border-radius: 5px !important;
}
[data-baseweb="select"] span { color: var(--jasmine) !important; font-family: 'Rajdhani', sans-serif !important; }
[data-baseweb="popover"] { background: var(--panel2) !important; border: 1px solid var(--red-b) !important; }
[data-baseweb="menu"] { background: var(--panel2) !important; }
[data-baseweb="option"]:hover { background: rgba(255,70,85,0.15) !important; }
[data-testid="stNumberInput"] button {
    background: var(--panel2) !important;
    border-color: rgba(255,70,85,0.25) !important;
    color: var(--jasmine) !important;
}
[data-testid="stDateInput"] > div > div { background: var(--panel2) !important; border-color: rgba(255,70,85,0.35) !important; }

/* ── custom message boxes ── */
.custom-box {
    background: var(--panel2);
    color: var(--jasmine);
    padding: 10px 14px;
    border-radius: 7px;
    margin-top: 6px;
    border-left: 3px solid var(--red-b);
    box-shadow: 0 3px 10px rgba(0,0,0,0.4);
    font-family: 'Cormorant Garamond', serif;
    font-style: italic;
    font-size: 15px;
    line-height: 1.5;
}

/* ── progress bar (hidden — replaced with custom HTML) ── */
[data-testid="stProgress"] { display: none !important; }

/* ── streak boxes ── */
.streak-box {
    color: var(--jasmine);
    padding: 14px 18px;
    border-radius: 10px;
    border: 1px solid;
    margin-bottom: 8px;
    box-shadow: 0 6px 18px rgba(0,0,0,0.45);
}
.streak-box .streak-label {
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    opacity: 0.75;
    margin-bottom: 4px;
}
.streak-box .big { font-size: 30px; font-weight: 800; line-height: 1; }
.streak-box .rank-sub { font-size: 11px; opacity: 0.6; margin-top: 4px; letter-spacing: 1px; text-transform: uppercase; }

/* ── rank tag ── */
.rank-tag {
    display: inline-block;
    background: var(--black);
    color: var(--red-b);
    border: 1px solid var(--red-b);
    border-radius: 3px;
    padding: 3px 10px;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-left: 6px;
    box-shadow: 0 0 8px rgba(255,70,85,0.2);
}

/* ── title ── */
.app-title {
    font-family: 'Saira Condensed', sans-serif;
    font-weight: 800;
    font-size: 46px;
    text-transform: uppercase;
    letter-spacing: 3px;
    color: var(--jasmine);
    text-shadow: 0 0 18px rgba(255,70,85,0.5), 2px 2px 0 rgba(0,0,0,0.6);
    transform: skewX(-5deg);
    display: inline-block;
    line-height: 1;
}
.app-title-underline {
    height: 3px;
    width: 240px;
    background: linear-gradient(90deg, var(--red-b), transparent);
    margin-top: 4px;
}

/* ── HUD banner ── */
.hud-banner {
    border-radius: 6px;
    padding: 9px 16px;
    margin: 8px 0 12px 0;
    font-weight: 700;
    font-size: 13px;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    border: 1px solid;
    box-shadow: 0 3px 10px rgba(0,0,0,0.4);
}

/* ── badge cards ── */
.badge-locked { opacity: 0.28; filter: grayscale(1); }
.badge-card {
    background: var(--panel);
    border: 1px solid rgba(255,70,85,0.25);
    border-radius: 8px;
    padding: 10px 6px;
    text-align: center;
    margin-bottom: 6px;
    box-shadow: 0 3px 10px rgba(0,0,0,0.35);
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.badge-card:hover { transform: translateY(-3px) scale(1.03); box-shadow: 0 8px 18px rgba(255,70,85,0.25); }
.badge-card .icon { font-size: 24px; }
.badge-card .name { color: var(--jasmine); font-size: 12px; font-weight: 700; margin-top: 4px; }
.badge-card .desc { color: var(--muted); font-size: 10px; font-family: 'Cormorant Garamond', serif; font-style: italic; }

/* ── custom table ── */
.ha-table { width: 100%; border-collapse: collapse; font-family: 'Rajdhani', sans-serif; font-size: 14px; }
.ha-table th {
    background: var(--red);
    color: var(--jasmine);
    padding: 7px 12px;
    text-align: left;
    font-size: 11px;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    font-weight: 700;
}
.ha-table td { padding: 7px 12px; border-bottom: 1px solid rgba(255,255,255,0.05); color: var(--jasmine); }
.ha-table tr:hover td { background: rgba(255,70,85,0.07); }
.ha-table tr:last-child td { border-bottom: none; }

/* ── misc ── */
hr { border-color: rgba(255,70,85,0.15) !important; margin: 0.5rem 0 !important; }
.block-container { padding-top: 1.8rem !important; padding-bottom: 2rem !important; }
[data-testid="stVerticalBlock"] { gap: 0.55rem !important; }
[data-testid="stRadio"] label { font-size: 13px !important; }
</style>
""", unsafe_allow_html=True)

# ---------- UI ----------
# Init + load
init_db()
data = load_data(_uid)
mood_data = load_moods(_uid)
stats = get_stats(data)
current_rank = get_rank(stats["current_streak"])

st.markdown(f"""
<div class="app-title-wrap">
  <div style="display:flex; align-items:center; gap:14px; flex-wrap:wrap;">
    <div class="app-title">HydrAgent</div>
    <span class="rank-tag">{current_rank}</span>
    <span style="font-family:Rajdhani,sans-serif; font-size:13px; color:{_ucolor};
                 letter-spacing:2px; text-transform:uppercase; margin-left:4px;">
      ● {_uname}
    </span>
  </div>
  <div class="app-title-underline"></div>
</div>
""", unsafe_allow_html=True)

if st.button("Switch user", key="logout"):
    st.session_state.user_id = None
    st.rerun()

# Anniversary + birthday messages
today_now = date.today()
anniversary_hits = get_anniversary_message(today_now)
for label, msg in anniversary_hits:
    if label == "Birthday":
        st.balloons()
        st.markdown(
            f"<div class='custom-box' style='border-left-color:#ffd23d; "
            f"background:linear-gradient(135deg,#2a1f00,#141414); "
            f"padding:18px 20px;'>"
            f"<div style='font-family:Saira Condensed,sans-serif; font-size:28px; font-weight:800; "
            f"color:#ffd23d; letter-spacing:2px; text-transform:uppercase; line-height:1.1;'>"
            f"Happy Birthday 🎂</div>"
            f"<div style='font-size:16px; margin-top:8px; color:#FFF6E0;'>{msg}</div></div>",
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"<div class='custom-box' style='border-left-color:#ffd23d; font-size:15px;'>"
            f"<b>{label}</b> — {msg}</div>",
            unsafe_allow_html=True
        )

# HUD status banner
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
    STATUS: {_label} — {_subtext} &nbsp;·&nbsp; GOAL: {DAILY_GOAL} ML
</div>
""", unsafe_allow_html=True)

RANK_COLORS = {
    "Iron": ("#3a3a3a", "#9a9a9a"),
    "Bronze": ("#3d2a1a", "#cd7f32"),
    "Silver": ("#2a2d30", "#c0c0c0"),
    "Gold": ("#3d3400", "#ffd700"),
    "Platinum": ("#1a2d2d", "#4fc3c3"),
    "Diamond": ("#1a1a3d", "#6a9de0"),
    "Ascendant": ("#1a2d1a", "#4fc34f"),
    "Immortal": ("#3d1a2d", "#c34f9d"),
    "Radiant": ("#3d2d00", "#ffd23d"),
}
streak_cols = st.columns(2)
with streak_cols[0]:
    _sbg, _sac = RANK_COLORS.get(current_rank, ("#2a0a0a", "#FF4655"))
    _grace_note = "<div class='rank-sub' style='color:#ff9d3d;'>⚠ close call yesterday</div>" if stats.get("grace_yesterday") else ""
    st.markdown(f"""
    <div class="streak-box" style="background:linear-gradient(135deg,{_sbg} 0%,#0A0A0A 100%); border-color:{_sac}; box-shadow:0 6px 18px {_sac}33;">
        <div class="streak-label" style="color:{_sac};">Current Streak</div>
        <div class="big" style="color:{_sac};">{stats['current_streak']} day{'s' if stats['current_streak'] != 1 else ''}</div>
        <div class="rank-sub" style="color:{_sac};">{current_rank}</div>
        {_grace_note}
    </div>
    """, unsafe_allow_html=True)
with streak_cols[1]:
    _best_rank = get_rank(stats["best_streak"])
    _bbg, _bac = RANK_COLORS.get(_best_rank, ("#2a0a0a", "#FF4655"))
    st.markdown(f"""
    <div class="streak-box" style="background:linear-gradient(135deg,{_bbg} 0%,#0A0A0A 100%); border-color:{_bac}; box-shadow:0 6px 18px {_bac}33;">
        <div class="streak-label" style="color:{_bac};">Best Streak</div>
        <div class="big" style="color:{_bac};">{stats['best_streak']} day{'s' if stats['best_streak'] != 1 else ''}</div>
        <div class="rank-sub" style="color:{_bac};">Peak: {_best_rank}</div>
    </div>
    """, unsafe_allow_html=True)

if stats.get("grace_yesterday"):
    yesterday = date.today() - timedelta(days=1)
    y_total = get_daily_total(data, yesterday)
    shortfall = DAILY_GOAL - y_total
    st.markdown(
        f"<div class='custom-box' style='border-left-color:#ff9d3d; font-size:13px;'>"
        f"⚠ Yesterday you hit <b>{y_total} ml</b> — only <b>{shortfall} ml</b> short of the goal. "
        f"Streak preserved for now. Don't make it a habit.</div>",
        unsafe_allow_html=True
    )

# view_date is needed below, so define it before the column split
view_date = st.date_input("View date", value=date.today())

# Layout — only put genuinely similar-sized content side by side.
# Everything longer (table, chart, briefings) goes full-width below so one
# column never ends up much taller than the other with a void beside it.
col1, col2 = st.columns(2)

# ---------- LEFT COLUMN: quick add + mood ----------
with col1:
    st.markdown(f'<div class="section-card-label">Buy Phase — Stock Up</div>', unsafe_allow_html=True)

    quick_amounts = [250, 500]
    quick_cols = st.columns(len(quick_amounts))
    for idx, amt in enumerate(quick_amounts):
        with quick_cols[idx]:
            if st.button(f"+{amt} ml", key=f"quick_{amt}"):
                now = add_entry(amt, _uid)
                data = load_data(_uid)
                stats = get_stats(data)
                announce_entry(amt, now, data)
                st.session_state.refresh += 1

    custom_amount = st.number_input("Or type amount (ml)", min_value=0, step=50, value=250)
    if st.button("Add entry"):
        if custom_amount <= 0:
            st.warning("Stop trying stupid things, lil bro")
        else:
            now = add_entry(custom_amount, _uid)
            data = load_data(_uid)
            stats = get_stats(data)
            announce_entry(custom_amount, now, data)
            st.session_state.refresh += 1

    st.markdown('<div class="divider"><div class="divider-diamond"></div></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="section-card-label">Daily Mood</div>', unsafe_allow_html=True)

    mood_data = load_moods(_uid)
    existing_score, existing_label, existing_note = get_mood_for_date(mood_data, date.today())

    if existing_label:
        st.caption("Update today's mood below:")

    mood_choice = st.selectbox(
        "How are you feeling today?",
        list(MOOD_OPTIONS.keys()),
        index=list(MOOD_OPTIONS.keys()).index(existing_label) if existing_label else 4,
        label_visibility="collapsed"
    )
    mood_note = st.text_input("Add a note (optional)", value=existing_note or "", placeholder="rough day, headache, good vibes...")
    if st.button("Log mood"):
        save_mood(date.today(), mood_choice, mood_note, _uid)
        st.success(f"Mood logged: {mood_choice}")
        st.session_state.refresh += 1

# ---------- RIGHT COLUMN: today's status ----------
with col2:
    st.markdown(f'<div class="section-card-label">Mission Status</div>', unsafe_allow_html=True)

    total_today = get_daily_total(data, view_date)
    st.write(f"Total for {view_date.isoformat()}: **{total_today} ml**")

    progress_val = min(total_today / DAILY_GOAL, 1)
    _pct = int(progress_val * 100)
    _bar_color = "#3ddc6f" if _pct >= 100 else "#FF4655" if _pct < 25 else "#ffd23d" if _pct < 60 else "#FF4655"
    st.markdown(f"""
    <div style="margin:6px 0 4px 0;">
        <div style="background:#1C1C1C; border-radius:4px; height:10px; overflow:hidden; border:1px solid rgba(255,255,255,0.08);">
            <div style="width:{_pct}%; height:100%; background:linear-gradient(90deg,{_bar_color},{_bar_color}cc);
                        border-radius:4px; transition:width 0.4s ease;"></div>
        </div>
        <div style="font-size:12px; color:#8A8070; margin-top:4px; letter-spacing:1px;">{_pct}% — {total_today} / {DAILY_GOAL} ML</div>
    </div>
    """, unsafe_allow_html=True)
    st.progress(progress_val)  # hidden by CSS, keeps Streamlit state happy

    # Hydration forecast
    _today_entries = data[data["Date"] == date.today()]
    _forecast, _on_track, _hrs_left = get_hydration_forecast(_today_entries, DAILY_GOAL)
    if _forecast is not None:
        _shortfall = max(0, DAILY_GOAL - _forecast)
        if _on_track:
            _fc_color = "#3ddc6f"
            _fc_msg = f"On track — forecast <b>{_forecast} ml</b> by midnight."
        else:
            _fc_color = "#ff9d3d"
            _fc_msg = (
                f"At this rate: <b>{_forecast} ml</b> by midnight. "
                f"Short by <b>{_shortfall} ml</b>. Pick up the pace."
            )
        st.markdown(
            f"<div class='custom-box' style='border-left-color:{_fc_color}; font-size:13px; margin-top:6px;'>"
            f"📈 {_fc_msg}</div>",
            unsafe_allow_html=True
        )

    # Best/worst day of week
    best_dow, worst_dow = get_weekly_best_worst(data)
    if best_dow and worst_dow:
        st.markdown('<div class="divider"><div class="divider-diamond"></div></div>', unsafe_allow_html=True)
        st.markdown(
            f"<div class='custom-box'>Best day: <b>{best_dow}</b><br>"
            f"Worst day: <b>{worst_dow}</b> — classic.</div>",
            unsafe_allow_html=True
        )

    # Notes log — shows all mood entries that have a note
    st.markdown('<div class="divider"><div class="divider-diamond"></div></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="section-card-label">Notes</div>', unsafe_allow_html=True)
    _notes_df = mood_data[
        mood_data["note"].notna() &
        (mood_data["note"].astype(str).str.strip() != "") &
        (mood_data["note"].astype(str) != "None")
    ].copy() if not mood_data.empty else pd.DataFrame()
    if not _notes_df.empty:
        _notes_df = _notes_df.sort_values("date", ascending=False)
        for _, _nr in _notes_df.iterrows():
            _nc = MOOD_COLORS.get(int(_nr["mood_score"]), "#FFF6E0")
            st.markdown(
                f"<div class='custom-box' style='border-left-color:{_nc}; margin-bottom:6px;'>"
                f"<span style='font-size:11px; color:#c9c0a8;'>{_nr['date']} · {_nr['mood_label']}</span><br>"
                f"{_nr['note']}</div>",
                unsafe_allow_html=True
            )
    else:
        st.caption("Notes you add when logging mood will appear here.")

    # Admin time-capsule messages — visible from their deliver_date onward
    _unlocked = get_unlocked_admin_messages()
    if not _unlocked.empty:
        st.markdown('<div class="divider"><div class="divider-diamond"></div></div>', unsafe_allow_html=True)
        st.markdown('<div class="section-card-label" style="color:#ffd23d;">Messages for you</div>', unsafe_allow_html=True)
        for _, _mr in _unlocked.iterrows():
            st.markdown(
                f"<div class='custom-box' style='border-left-color:#ffd23d; "
                f"background:linear-gradient(135deg,#1a1400,#141414);'>"
                f"<span style='font-size:10px; color:#8A8070; letter-spacing:1px;'>{_mr['deliver_date']}</span><br>"
                f"{_mr['message']}</div>",
                unsafe_allow_html=True
            )

# ---------- FULL-WIDTH: Match History ----------
st.markdown('<div class="divider"><div class="divider-diamond"></div></div>', unsafe_allow_html=True)
st.markdown(f'<div class="section-card-label">Match History — {view_date.isoformat()}</div>', unsafe_allow_html=True)
data = load_data(_uid)
view_df = data[data["Date"] == view_date].copy()

if not view_df.empty:
    view_df_display = view_df.copy()
    view_df_display["Time"] = view_df_display["Time"].apply(
        lambda t: datetime.strptime(str(t), "%H:%M:%S").strftime("%I:%M %p")
    )

    rows_html = "".join(
        f"<tr><td>{int(r['id'])}</td><td>{r['Time']}</td>"
        f"<td>{int(r['Amount (ml)'])} ml</td></tr>"
        for _, r in view_df_display.iterrows()
    )
    st.markdown(f"""
    <table class="ha-table">
        <thead><tr><th>ID</th><th>Time</th><th>Amount</th></tr></thead>
        <tbody>{rows_html}</tbody>
    </table>
    """, unsafe_allow_html=True)

    to_delete = st.multiselect("Select rows to delete (ID)", view_df_display["id"])

    if st.button("Delete selected"):
        if to_delete:
            delete_entries(to_delete, _uid)
            st.success("Deleted selected entries.")
            st.session_state.refresh += 1
        else:
            st.warning("Pick at least one row to delete.")
else:
    st.write("No entries for this date yet. Add one above!")

# ---------- FULL-WIDTH: unified water + mood dual-axis chart ----------
import calendar
st.markdown('<div class="divider"><div class="divider-diamond"></div></div>', unsafe_allow_html=True)
st.markdown(f'<div class="section-card-label">Water & Mood</div>', unsafe_allow_html=True)

_now = datetime.now(TZ)
view_mode = st.radio("Period", ["Last 7 days", "Monthly"], horizontal=True, label_visibility="collapsed")

if view_mode == "Last 7 days":
    _dates_range, _totals_range = get_history_aggregated(data)
    _chart_dates = [d.isoformat() for d in _dates_range]
    _water_vals = _totals_range
    _mood_rows = load_moods(_uid)
    _mood_map = {str(r["date"]): r["mood_score"] for _, r in _mood_rows.iterrows()} if not _mood_rows.empty else {}
    _mood_vals = [_mood_map.get(d) for d in _chart_dates]
    _label_angle = 0
    _rc_month = _now.month
    _rc_year = _now.year
else:
    _mc, _yc = st.columns([2, 1])
    with _mc:
        _rc_month = st.selectbox("Month", list(range(1, 13)),
            index=_now.month - 1,
            format_func=lambda m: datetime(2000, m, 1).strftime("%B"))
    with _yc:
        _rc_year = st.number_input("Year", min_value=2020, max_value=_now.year, value=_now.year)
    _, _dim = calendar.monthrange(_rc_year, _rc_month)
    _month_dates = [date(_rc_year, _rc_month, d) for d in range(1, _dim + 1)]
    _chart_dates = [d.isoformat() for d in _month_dates]
    _water_vals = [get_daily_total(data, d) for d in _month_dates]
    _mmdf = get_monthly_mood(load_moods(), _rc_year, _rc_month)
    _mood_map = {str(r["date"]): r["mood_score"] for _, r in _mmdf.iterrows()} if not _mmdf.empty else {}
    _mood_vals = [_mood_map.get(d) for d in _chart_dates]
    _label_angle = -45

_y_water_max = max(DAILY_GOAL, max(_water_vals) if _water_vals else 0)

_unified_df = pd.DataFrame({
    "date": _chart_dates,
    "water_ml": _water_vals,
    "mood_score": _mood_vals,
})

# Water bars — left axis
_water_bars = (
    alt.Chart(_unified_df)
    .mark_bar(color="#FF4655", opacity=0.85, cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
    .encode(
        x=alt.X("date:N", sort=None, title=None,
                axis=alt.Axis(labelColor="#FFF6E0", labelAngle=_label_angle, labelFontSize=10)),
        y=alt.Y("water_ml:Q",
                title="ml",
                scale=alt.Scale(domain=[0, _y_water_max]),
                axis=alt.Axis(
                    labelColor="#FF4655", titleColor="#FF4655", orient="left",
                    titleAngle=0, titleAlign="right", titleX=-8, titleY=-8,
                    labelPadding=4,
                )),
    )
)

# Goal line — tied to water scale, axis=None prevents it spawning its own right-side axis
_goal_df = pd.DataFrame({"date": _chart_dates, "water_ml": [DAILY_GOAL] * len(_chart_dates)})
_goal_line = (
    alt.Chart(_goal_df)
    .mark_line(color="#FFF6E0", strokeDash=[5, 5], opacity=0.35, strokeWidth=1.5)
    .encode(
        x=alt.X("date:N", sort=None),
        y=alt.Y("water_ml:Q", scale=alt.Scale(domain=[0, _y_water_max]), axis=None),
    )
)

# Mood line — right axis, independent scale
_mood_plot_df = _unified_df.dropna(subset=["mood_score"]).copy()
_mood_line = (
    alt.Chart(_mood_plot_df)
    .mark_line(color="#ffd23d", strokeWidth=2.5,
               point=alt.OverlayMarkDef(color="#ffd23d", size=70, filled=True))
    .encode(
        x=alt.X("date:N", sort=None),
        y=alt.Y("mood_score:Q",
                title="mood",
                scale=alt.Scale(domain=[1, 10]),
                axis=alt.Axis(
                    labelColor="#ffd23d", titleColor="#ffd23d", orient="right",
                    titleAngle=0, titleAlign="left", titleX=8, titleY=-8,
                    labelPadding=4, tickCount=9,
                )),
    )
)

_unified_chart = (
    alt.layer(_water_bars, _goal_line, _mood_line)
    .resolve_scale(y="independent")
    .properties(height=300, padding={"left": 70, "right": 70, "top": 20, "bottom": 10})
    .configure_view(strokeWidth=0, fill="#0D0D0D")
    .configure_axis(grid=True, gridColor="#222222")
)
st.altair_chart(_unified_chart, use_container_width=True)
st.caption("Red bars = water (ml, left axis)  ·  Yellow line = mood 1–10 (right axis)  ·  Dashed white = daily goal")

# ---------- Intel Briefing + Captain Holt's Briefing, side by side ----------
st.markdown('<div class="divider"><div class="divider-diamond"></div></div>', unsafe_allow_html=True)
intel_col, holt_col = st.columns(2)

with intel_col:
    st.markdown(f'<div class="section-card-label">Intel Briefing — Week vs Week</div>', unsafe_allow_html=True)
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
    st.markdown('<div class="section-card-label">Captain Holt&#39;s Briefing</div>', unsafe_allow_html=True)
    today_entries = data[data["Date"] == date.today()]
    escalation_msg = get_escalation_message(today_entries)
    st.markdown(f"<div class='custom-box' style='border-left-color:#FF4655;'>{escalation_msg}</div>", unsafe_allow_html=True)
    meme = random.choice(MEMES)
    st.markdown(
        f"<img src='{meme['url']}' style='width:100%; border-radius:8px; border:1px solid var(--jw-red); margin-top:8px;' />",
        unsafe_allow_html=True
    )
    msg = random.choice(MESSAGES)
    st.markdown(f"<div class='custom-box'>{msg['message']}</div>", unsafe_allow_html=True)

# Report card — uses the selected month/year from the chart toggle above
report = get_report_card(data, load_moods(), _rc_year, _rc_month)
if report:
    st.markdown('<div class="divider"><div class="divider-diamond"></div></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="section-card-label">Report Card — {datetime(_rc_year, _rc_month, 1).strftime('%B %Y')}</div>', unsafe_allow_html=True)
    grade_colors = {"S": "#ffd23d", "A": "#3ddc6f", "B": "#a8e06a", "C": "#ffd23d", "D": "#ff9d3d", "F": "#ff4655"}
    gc = grade_colors.get(report["grade"], "#FFF6E0")
    rc1, rc2 = st.columns([1, 3])
    with rc1:
        st.markdown(
            f"<div style='text-align:center; background:var(--jw-panel); border:2px solid {gc}; "
            f"border-radius:12px; padding:18px 0;'>"
            f"<div style='font-family:Saira Condensed,sans-serif; font-size:72px; font-weight:800; color:{gc}; line-height:1;'>"
            f"{report['grade']}</div>"
            f"<div style='color:#c9c0a8; font-size:12px; margin-top:4px;'>Grade</div></div>",
            unsafe_allow_html=True
        )
    with rc2:
        mood_line = f"<br>Avg mood: <b>{report['avg_mood']:.1f} / 10</b>" if report["avg_mood"] else ""
        st.markdown(
            f"<div class='custom-box' style='border-left-color:{gc}; height:100%;'>"
            f"<i>{report['verdict']}</i><br><br>"
            f"Goal hit: <b>{report['days_hit']} / {report['total_days']} days "
            f"({report['hit_rate']*100:.0f}%)</b><br>"
            f"Avg intake: <b>{report['avg_water']:.0f} ml/day</b>"
            f"{mood_line}</div>",
            unsafe_allow_html=True
        )


# ---------- BADGES ----------
st.markdown('<div class="divider"><div class="divider-diamond"></div></div>', unsafe_allow_html=True)
st.markdown(f'<div class="section-card-label">Loadout Unlocks</div>', unsafe_allow_html=True)
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
st.markdown('<div class="divider"><div class="divider-diamond"></div></div>', unsafe_allow_html=True)
if st.checkbox("Show raw data (DB)"):
    st.dataframe(load_data(), use_container_width=True)

# ---------- LEADERBOARD ----------
st.markdown('<div class="divider"><div class="divider-diamond"></div></div>', unsafe_allow_html=True)
st.markdown('<div class="section-card-label">Head to Head</div>', unsafe_allow_html=True)

_lb_cols = st.columns(2)
for _i, (_luid, _ludata) in enumerate(USERS.items()):
    _ldata = load_data(_luid)
    _lstats = get_stats(_ldata)
    _lrank = get_rank(_lstats["current_streak"])
    _lcolor = _ludata["color"]
    _lbg, _lac = RANK_COLORS.get(_lrank, ("#2a0a0a", _lcolor))
    _is_you = _luid == _uid
    with _lb_cols[_i]:
        st.markdown(f"""
        <div class="streak-box" style="background:linear-gradient(135deg,{_lbg} 0%,#0A0A0A 100%);
             border-color:{_lcolor}; box-shadow:0 6px 18px {_lcolor}33;">
            <div class="streak-label" style="color:{_lcolor};">
                {_ludata['name']} {'· you' if _is_you else ''}
            </div>
            <div class="big" style="color:{_lcolor};">{_lstats['current_streak']}d streak</div>
            <div class="rank-sub" style="color:{_lcolor};">{_lrank}</div>
            <div class="rank-sub" style="color:#8A8070; margin-top:4px;">
                {_lstats['lifetime_ml'] // 1000}L lifetime · {_lstats['days_hit_goal']} goal days
            </div>
        </div>
        """, unsafe_allow_html=True)

# ---------- ADMIN PANEL (hidden, password-gated) ----------
st.markdown('<div class="divider"><div class="divider-diamond"></div></div>', unsafe_allow_html=True)
with st.expander("⚙ Admin"):
    _pw = st.text_input("Password", type="password", label_visibility="collapsed", placeholder="Password")
    if _pw == ADMIN_PASSWORD:
        st.markdown('<div class="section-card-label">Write a time-capsule message</div>', unsafe_allow_html=True)
        _am_date = st.date_input("Deliver on", value=date.today() + timedelta(days=1), key="admin_date")
        _am_text = st.text_area("Message", placeholder="Write something they'll see on that date...", key="admin_msg")
        if st.button("Schedule message", key="admin_send"):
            if _am_text.strip():
                save_admin_message(_am_date, _am_text.strip())
                st.success(f"Scheduled for {_am_date.isoformat()}")
            else:
                st.warning("Message can't be empty.")

        st.markdown('<div class="section-card-label" style="margin-top:14px;">Scheduled messages</div>', unsafe_allow_html=True)
        _all_msgs = get_all_admin_messages()
        if not _all_msgs.empty:
            for _, _mr in _all_msgs.iterrows():
                _status = "✓ delivered" if _mr["delivered"] else "pending"
                _sc = "#3ddc6f" if _mr["delivered"] else "#ffd23d"
                st.markdown(
                    f"<div class='custom-box' style='border-left-color:{_sc}; font-size:13px;'>"
                    f"<span style='color:#8A8070; font-size:11px;'>{_mr['deliver_date']} · {_status}</span><br>"
                    f"{_mr['message']}</div>",
                    unsafe_allow_html=True
                )
        else:
            st.caption("No messages scheduled yet.")
    elif _pw:
        st.error("Wrong password.")
