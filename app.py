import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import os
import random
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

CSV_FILE = "data.csv"
DAILY_GOAL = 2000  # ml
HISTORY_DAYS = 7
TZ = pytz.timezone("Etc/GMT-4")  # Set timezone

# ---------- MESSAGES ----------
MESSAGES = [
    {"type":"Roast", "message":"Drink water before your organs file a complaint."},
    {"type":"Roast", "message":"Your cells are crispier than KFC."},
    {"type":"Quotes", "message":"Proud of you for hydrating (even a little)."},
    {"type":"Maths", "message":"I wouldn't mind you being dehydrated but fainting is kinda my thing 🙄"},
    {"type":"HIMYM", "message":"You’re the Barney of hydration — full of promises, no delivery."},
    {"type":"Council", "message":"🧘ye deekho chookari maar ke aapke paani peene ka intezaar."}
]

# ---------- MEMES ----------
MEMES = [
    {"url":"https://i.imgflip.com/aaiih1.jpg","caption":""},
    {"url":"https://i.imgflip.com/aaiinq.jpg","caption":""},
    {"url":"https://i.imgflip.com/aaijhu.jpg","caption":""},
    {"url":"https://i.imgflip.com/aailz2.jpg","caption":""},
    {"url":"https://i.imgflip.com/aaim2z.jpg","caption":""},
    {"url":"https://i.imgflip.com/aaimit.jpg","caption":""},
    {"url":"https://i.imgflip.com/aaios5.jpg","caption":""},
    {"url":"https://i.pinimg.com/1200x/6a/dd/a7/6adda7b08880e234247df0c566b8ebc3.jpg","caption":"kiun nhin pi rhe aap paani."},
    {"url":"https://i.pinimg.com/1200x/3e/31/7f/3e317fdabd3c015819e6e096ca030e7f.jpg","caption":"You're not the only one with cameras."},
    {"url":"https://i.pinimg.com/1200x/b2/af/75/b2af75f216dd5cd75379789beff5b8a1.jpg","caption":"imagine fardan living longer than you cause he drank water and you didn't."},
    {"url":"https://i.pinimg.com/736x/37/c1/4c/37c14ca7f0d61a2a8db4788c09dd336b.jpg","caption":"me if u dont drink water."},
    {"url":"https://i.pinimg.com/736x/97/74/cd/9774cd9bd7daead2ac764adb34a0e72f.jpg","caption":"your mom if u need to go to the doc again."},
    {"url":"https://i.imgflip.com/ab2rs7.jpg","caption":""},
    {"url":"https://i.imgflip.com/ab2s52.jpg","caption":""},
    {"url":"https://i.imgflip.com/ab2seh.jpg","caption":""},
    {"url":"https://i.imgflip.com/ab2sld.jpg","caption":""},
    {"url":"https://i.imgflip.com/ab2sup.jpg","caption":""},
    {"url":"https://i.imgflip.com/ab2syj.jpg","caption":""},
    {"url":"https://i.imgflip.com/ab2t61.jpg","caption":""},
    {"url":"https://i.imgflip.com/ab2thh.jpg","caption":""},
    {"url":"https://i.imgflip.com/ab2tqs.jpg","caption":""},
    {"url":"https://i.imgflip.com/ab2ttv.jpg","caption":""},
    {"url":"https://i.imgflip.com/ab2txr.jpg","caption":""}
]

# ---------- HELPERS ----------
def init_csv():
    """Ensure CSV exists and has correct structure."""
    if not os.path.exists(CSV_FILE):
        df = pd.DataFrame(columns=["Date", "Time", "Amount (ml)"])
        df.to_csv(CSV_FILE, index=False)
        return df

    df = pd.read_csv(CSV_FILE)

    # Fix old 2-column format → migrate safely
    if list(df.columns) == ["Date", "Water Intake (ml)"]:
        migrated = pd.DataFrame(columns=["Date", "Time", "Amount (ml)"])
        for _, row in df.iterrows():
            d = pd.to_datetime(row["Date"], errors='coerce')
            d = d.date() if not pd.isna(d) else row["Date"]
            migrated.loc[len(migrated)] = [d, "00:00:00", row["Water Intake (ml)"]]
        migrated.to_csv(CSV_FILE, index=False)
        return migrated

    # If wrong columns → reset
    if set(df.columns) != {"Date", "Time", "Amount (ml)"}:
        df = pd.DataFrame(columns=["Date", "Time", "Amount (ml)"])
        df.to_csv(CSV_FILE, index=False)

    return df


def load_data():
    """Load CSV safely with correct parsing."""
    df = pd.read_csv(CSV_FILE)

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce").dt.date
    df["Time"] = pd.to_datetime(df["Time"], errors="coerce").dt.time
    df["Time"] = df["Time"].fillna(datetime.strptime("00:00:00", "%H:%M:%S").time())

    df["Amount (ml)"] = (
        pd.to_numeric(df["Amount (ml)"], errors="coerce")
        .fillna(0)
        .astype(int)
    )

    return df


def save_data(df):
    """Save CSV with safe string formats."""
    df2 = df.copy()
    df2["Date"] = df2["Date"].astype(str)
    df2["Time"] = df2["Time"].astype(str)
    df2.to_csv(CSV_FILE, index=False)


def add_entry(amount_ml):
    now = datetime.now(TZ)
    new_row = {
        "Date": now.date(),
        "Time": now.time().replace(microsecond=0).isoformat(),
        "Amount (ml)": int(amount_ml)
    }
    df = load_data()
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    save_data(df)
    return now


def delete_entries(indices):
    df = load_data()
    if not indices:
        return False
    df = df.drop(index=indices).reset_index(drop=True)
    save_data(df)
    return True


def get_daily_total(df, target_date):
    return int(df[df["Date"] == target_date]["Amount (ml)"].sum())


def get_history_aggregated(df, days=HISTORY_DAYS):
    today = date.today()
    dates = [today - timedelta(days=i) for i in range(days-1, -1, -1)]
    totals = [get_daily_total(df, d) for d in dates]
    return dates, totals


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

# Load data
init_csv()
data = load_data()

# Sidebar
with st.sidebar:
    st.header("Random stuff you dont need to worry about.")
    st.write("Daily goal:", f"**{DAILY_GOAL} ml**")
    reminder_toggle = st.checkbox("Enable in-app reminders while app is open", value=False)
    reminder_interval = st.number_input("Reminder interval (minutes)", min_value=1, max_value=1440, value=60)
    st.markdown("---")
    st.write("Theme:")
    theme_choice = st.radio("", ["Funny & chaotic", "Minimal & calm"], index=0)

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
                st.success(f"Added {amt} ml at {now.strftime('%I:%M %p')}")
                meme = random.choice(MEMES)
                st.image(meme["url"], use_container_width=True)
                st.session_state.refresh += 1

    # Custom input
    custom_amount = st.number_input("Or type amount (ml)", min_value=0, step=50, value=250)
    if st.button("Add entry"):
        if custom_amount <= 0:
            st.warning("Stop trying stupid things, lil bro")
        else:
            now = add_entry(custom_amount)
            st.success(f"Added {custom_amount} ml at {now.strftime('%I:%M %p')}")
            data = load_data()

            total_today = get_daily_total(data, date.today())
            if total_today >= DAILY_GOAL:
                st.success("🎉 HYDRATION SUPREMACY! You hit today's goal!")

            meme = random.choice(MEMES)
            st.image(meme["url"], use_container_width=True)

            msg = random.choice(MESSAGES)
            st.markdown(f"<div class='custom-box'>{msg['message']}</div>", unsafe_allow_html=True)

            st.session_state.refresh += 1

    st.markdown("---")
    view_date = st.date_input("View date", value=date.today())

    # Logs
    st.subheader(f"Logs for {view_date.isoformat()}")
    data = load_data()
    view_df = data[data["Date"] == view_date].copy()

    if not view_df.empty:
        view_df_display = view_df.reset_index().rename(columns={"index": "row_index"})
        view_df_display["ID"] = view_df_display["row_index"] + 1

        # Display time in clean 12hr format
        view_df_display["Time"] = view_df_display["Time"].apply(
            lambda t: datetime.strptime(str(t), "%H:%M:%S").strftime("%I:%M %p")
        )

        st.dataframe(
            view_df_display[["ID", "Time", "Amount (ml)"]],
            use_container_width=True
        )

        to_delete = st.multiselect("Select rows to delete (ID)", view_df_display["ID"])
        real_ids = [
            view_df_display.loc[view_df_display["ID"] == i, "row_index"].values[0]
            for i in to_delete
        ]

        if st.button("Delete selected"):
            if real_ids:
                delete_entries(real_ids)
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
if st.checkbox("Show raw data (CSV)"):
    st.dataframe(load_data(), use_container_width=True)
