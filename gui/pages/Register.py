import streamlit as st
import psycopg2

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

# 2. Sidebar i Wylogowanie (dla spójności, choć nie będzie użyte)

st.title("📝 Rejestracja")

first_name = st.text_input("Imię")
last_name = st.text_input("Nazwisko")
email = st.text_input("Email")
password = st.text_input("Hasło", type="password")

if st.button("Zarejestruj"):
    if not all([first_name, last_name, email, password]):
        st.error("Wszystkie pola są wymagane.")
    else:
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO customers (first_name, last_name, email, password)
                VALUES (%s, %s, %s, %s)
            """, (first_name, last_name, email, password))
            conn.commit()
            cur.close()
            conn.close()
            st.success("Konto zostało utworzone! Możesz się teraz zalogować.")
        except psycopg2.errors.UniqueViolation:
            st.error("Adres email jest już używany.")
        except Exception as e:
            st.error(f"Błąd: {e}")