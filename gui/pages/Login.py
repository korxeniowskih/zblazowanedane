import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor

# --- Konfiguracja bazy i Globalna Logika Sesji ---
DB_CONFIG = {
    "dbname": "kino",
    "user": "web",
    "password": "web",
    "host": "db",
    "port": "5432"
}

def get_db():
    return psycopg2.connect(**DB_CONFIG)

# 1. Sprawdzenie, czy użytkownik jest już zalogowany
if "logged" in st.session_state and st.session_state["logged"]:
    # Jeśli zalogowany, przenieś na główną stronę aplikacji
    st.switch_page("pages/Rezerwacje.py")

# 2. Sidebar i Wylogowanie (wyświetla się, gdy użytkownik jest zalogowany, ale kod nie jest osiągany, bo nastąpi przekierowanie)
# To jest potrzebne, by Streamlit zainicjował sesję na każdej stronie.

st.title("🔐 Logowanie")

email = st.text_input("Email")
password = st.text_input("Hasło", type="password")

if st.button("Zaloguj"):
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT id, first_name, last_name, password 
        FROM customers
        WHERE email = %s
    """, (email,))

    user = cur.fetchone()
    cur.close()
    conn.close()

    if user is None:
        st.error("Nie znaleziono użytkownika o tym adresie email.")
    elif user["password"] != password:
        st.error("Niepoprawne hasło.")
    else:
        st.success(f"Witaj, {user['first_name']}!")

        # zapis do sesji
        st.session_state["logged"] = True
        st.session_state["user_id"] = user["id"]
        st.session_state["user_name"] = user["first_name"]

        # przejście do podstrony po zalogowaniu
        st.switch_page("pages/Rezerwacje.py")