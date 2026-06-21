import streamlit as st
import pandas as pd
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
TZ = pytz.timezone("Asia/Karachi")  # fixed: was Etc/GMT-4 (UTC+4), Karachi is UTC+5

# ---------- MESSAGES ----------
MESSAGES = [
    {"type": "Roast", "message": "Drink water before your organs file a complaint."},
    {"type": "Roast", "message": "Your cells are crispier than KFC."},
    {"type": "Quotes", "message": "Proud of you for hydrating (even a little)."},
    {"type": "Maths", "message": "I wouldn't mind you being dehydrated but fainting is kinda my thing 🙄"},
    {"type": "HIMYM", "message": "You're the Barney of hydration — full of promises, no delivery."},
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

    # One-time migration from the old CSV-based version, if it exists and the table is empty
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
                    pass  # don't block app startup over a failed migration


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


def announce_entry(amount, now, data_after):
    """Shared success/meme/message block used by both quick-add and custom-add."""
    st.success(f"Added {amount} ml at {now.strftime('%I:%M %p')}")

    total_today = get_daily_total(data_after, date.today())
    if total_today >= DAILY_GOAL:
        st.success("🎉 HYDRATION SUPREMACY! You hit today's goal!")

    meme = random.choice(MEMES)
    st.image(meme["url"], use_container_width=True)

    msg = random.choice(MESSAGES)
    st.markdown(f"<div class='custom-box'>{msg['message']}</div>", unsafe_allow_html=True)


# ---------- SESSION ----------
if "refresh" not in st.session_state:
    st.session_state.refresh = 0

# ---------- CSS ----------
st.markdown("""
<style>
div.stButton > button {
    min-width: 90px;
    padding: 8px 0px;
    font-size: 16px;
    margin: 2px 0px;
}
.custom-box {
    background-color: #f5faff;
    color: black;
    padding: 10px;
    border-radius: 8px;
    margin-top: 8px;
}
</style>
""", unsafe_allow_html=True)

# ---------- UI ----------
st.markdown("""
<div style="display:flex; align-items:center; gap:12px;">
  <div style="font-size:28px;">💧</div>
  <div style="font-size:30px; font-weight:600;">WaterYouDoing</div>
</div>
""", unsafe_allow_html=True)

# Init + load
init_db()
data = load_data()

# Sidebar (reminder controls removed — they weren't wired to anything)
with st.sidebar:
    st.header("Random stuff you dont need to worry about.")
    st.write("Daily goal:", f"**{DAILY_GOAL} ml**")
    st.markdown("---")
    st.write("Theme:")
    theme_choice = st.radio("", ["Funny & chaotic", "Minimal & calm"], index=0)

# view_date is needed by both columns, so define it before the column split
view_date = st.date_input("View date", value=date.today())

# Layout
col1, col2 = st.columns([1.5, 1])

# ---------- LEFT COLUMN ----------
with col1:
    st.subheader("Add water intake")

    # Quick buttons
    quick_amounts = [250, 500]
    quick_cols = st.columns(len(quick_amounts))
    for idx, amt in enumerate(quick_amounts):
        with quick_cols[idx]:
            if st.button(f"+{amt} ml", key=f"quick_{amt}"):
                now = add_entry(amt)
                data = load_data()
                announce_entry(amt, now, data)
                st.session_state.refresh += 1

    # Custom input
    custom_amount = st.number_input("Or type amount (ml)", min_value=0, step=50, value=250)
    if st.button("Add entry"):
        if custom_amount <= 0:
            st.warning("Stop trying stupid things, lil bro")
        else:
            now = add_entry(custom_amount)
            data = load_data()
            announce_entry(custom_amount, now, data)
            st.session_state.refresh += 1

    st.markdown("---")

    # Logs
    st.subheader(f"Logs for {view_date.isoformat()}")
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

# ---------- RIGHT COLUMN ----------
with col2:
    st.subheader("Imagine not drinking water.")

    total_today = get_daily_total(data, view_date)
    st.write(f"Total for {view_date.isoformat()}: **{total_today} ml**")

    progress_val = min(total_today / DAILY_GOAL, 1)
    st.progress(progress_val)
    st.write(f"{int(progress_val * 100)}% of {DAILY_GOAL} ml")

    st.markdown("---")
    dates, totals = get_history_aggregated(data)
    chart_df = pd.DataFrame({"date": [d.isoformat() for d in dates], "total": totals})
    st.write("Last week of cat's water rehab:")
    st.bar_chart(chart_df.set_index("date")["total"])

    st.markdown("---")
    st.subheader("Ominous motivation.")
    st.write("Your drinking habits are not up to the mark.")

    if theme_choice == "Funny & chaotic":
        meme = random.choice(MEMES)
        st.image(meme["url"], use_container_width=True)
        msg = random.choice(MESSAGES)
        st.markdown(f"<div class='custom-box'>{msg['message']}</div>", unsafe_allow_html=True)
    else:
        calm_msgs = [
            "Small steps — sip-by-sip.",
            "Consistency > intensity.",
            "One glass at a time."
        ]
        st.markdown(f"<div class='custom-box'>{random.choice(calm_msgs)}</div>", unsafe_allow_html=True)

# Raw data toggle
st.markdown("---")
if st.checkbox("Show raw data (DB)"):
    st.dataframe(load_data(), use_container_width=True)
