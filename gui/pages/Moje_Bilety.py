import streamlit as st
import psycopg2
import pandas as pd
from psycopg2.extras import RealDictCursor

DB_CONFIG = {
    "dbname": "kino",
    "user": "web",
    "password": "web",
    "host": "db",
    "port": "5432"
}

def get_db():
    return psycopg2.connect(**DB_CONFIG)

# --- GLOBALNA LOGIKA SIDEBAR I WYLOGOWANIE ---
if "logged" in st.session_state and st.session_state["logged"]:
    with st.sidebar:
        st.success(f"Zalogowano jako: {st.session_state['user_name']}")
        if st.button("Wyloguj"):
            del st.session_state["logged"]
            del st.session_state["user_id"]
            del st.session_state["user_name"]
            st.switch_page("Login.py") # Przekierowanie do Login.py po wylogowaniu

# --- KONTROLA DOSTĘPU ---
if "logged" not in st.session_state or not st.session_state["logged"]:
    st.error("Musisz się zalogować, aby zobaczyć tę stronę.")
    st.page_link("pages/Login.py", label="Przejdź do strony Logowania")
    st.stop()

st.title("🎫 Moje Bilety")
st.write(f"Witaj, **{st.session_state['user_name']}**!")

customer_id = st.session_state["user_id"] # ID klienta jest pobierane po przejściu kontroli dostępu

conn = get_db()

# 🚀 Pobranie biletów z widoku
df = pd.read_sql(
    f"""
    SELECT 
        movie_title,
        hall_name,
        start_time,
        end_time,
        price_cents,
        status
    FROM view_customer_tickets
    WHERE customer_id = {customer_id}
    ORDER BY start_time DESC
    """,
    conn
)

conn.close()

if df.empty:
    st.info("Nie masz żadnych biletów.")
else:
    df["Data seansu"] = df["start_time"].dt.strftime("%Y-%m-%d %H:%M")
    df["Cena (PLN)"] = df["price_cents"] / 100
    df = df[["movie_title", "hall_name", "Data seansu", "Cena (PLN)", "status"]]

    st.subheader("Twoje bilety")
    st.dataframe(df, use_container_width=True, hide_index=True)