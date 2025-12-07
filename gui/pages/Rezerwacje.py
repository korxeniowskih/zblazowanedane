import streamlit as st
import psycopg2
import pandas as pd

DB_CONFIG = {
    "dbname": "kino",
    "user": "admin",
    "password": "admin",
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
            st.switch_page("pages/Login.py") # Przekierowanie do Login.py po wylogowaniu

# --- KONTROLA DOSTĘPU ---
if "logged" not in st.session_state or not st.session_state["logged"]:
    st.error("Musisz się zalogować, aby zobaczyć tę stronę.")
    st.page_link("pages/Login.py", label="Przejdź do strony Logowania")
    st.stop()

st.title("🎬 Rezerwacja filmów")
st.write(f"Witaj, **{st.session_state['user_name']}**!")

conn = get_db()

# 🚀 Pobranie seansów z widoku
screenings = pd.read_sql(
    """
    SELECT *
    FROM view_screenings_with_movie
    WHERE start_time > NOW()
    ORDER BY movie_title, start_time
    """,
    conn
)

if screenings.empty:
    st.info("Brak dostępnych seansów.")
    conn.close()
    st.stop()

# Grupowanie po filmach
movies = screenings["movie_title"].unique()
selected_movie = st.selectbox("Wybierz film:", movies)

movie_screenings = screenings[screenings["movie_title"] == selected_movie]

# Pokazanie szczegółów filmu (pierwszy seans z widoku zawiera je wszystkie)
genre = movie_screenings.iloc[0]["genre"]
st.write(f"🎭 Gatunek: {genre}")

# Wybór seansu
options = {
    f"{row['start_time'].strftime('%Y-%m-%d %H:%M')} — sala {row['hall_name']} (Cena: {row['base_price_cents']/100:.2f} PLN)": row
    for _, row in movie_screenings.iterrows()
}

selected_label = st.selectbox("Wybierz seans:", list(options.keys()))
selected = options[selected_label]

st.subheader("Wybór miejsca")

# 🚀 Pobranie statusu miejsc z widoku view_seat_status
seat_df = pd.read_sql(
    f"""
    SELECT *
    FROM view_seat_status
    WHERE screening_id = {selected["screening_id"]}
    ORDER BY hall_id, row_label, seat_number
    """,
    conn
)

# Tylko miejsca wolne
free_seats = seat_df[seat_df["status"] == "free"]

if free_seats.empty:
    st.warning("Brak wolnych miejsc na ten seans.")
    conn.close()
    st.stop()

seat_options = {
    f"Rząd {row['row_label']} | Miejsce {row['seat_number']}": row
    for _, row in free_seats.iterrows()
}

selected_seat_label = st.selectbox("Wybierz miejsce:", list(seat_options.keys()))
selected_seat = seat_options[selected_seat_label]

if st.button("Kup bilet"):
    try:
        cur = conn.cursor()
        
        # NOTE: DANE Z PANDAS MUSZĄ BYĆ RZUTOWANE NA INT!
        screening_id = int(selected["screening_id"])
        seat_id = int(selected_seat["seat_id"])
        price_cents = int(selected["base_price_cents"])
        customer_id = int(st.session_state["user_id"])
        
        cur.execute(
            """
            INSERT INTO tickets (screening_id, seat_id, customer_id, price_cents, status)
            VALUES (%s, %s, %s, %s, 'sold')
            """,
            (
                screening_id,
                seat_id,
                customer_id,
                price_cents,
            )
        )
        conn.commit()
        st.success("🎉 Bilet został kupiony!")
        st.switch_page("pages/Moje_Bilety.py") # Zmieniono na poprawną ścieżkę
    except Exception as e:
        conn.rollback()
        st.error(f"Błąd podczas zakupu: {e}")
    finally:
        conn.close()
else:
    conn.close()