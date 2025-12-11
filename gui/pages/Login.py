import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
from nav_pages import rezerwacje_page

DB_CONFIG = {
    "dbname": "kino",
    "user": "web",
    "password": "web",
    "host": "db",
    "port": "5432"
}

def get_db():
    return psycopg2.connect(**DB_CONFIG)

# Jeśli już zalogowany, od razu przekieruj na Rezerwacje
if st.session_state.get("logged", False):
    st.switch_page(rezerwacje_page)

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

        st.session_state["logged"]    = True
        st.session_state["user_id"]   = user["id"]
        st.session_state["user_name"] = user["first_name"]
        if email == "admin":   # tu wstaw swój adminowy mail
            st.session_state["is_admin"] = True
        else:
            st.session_state["is_admin"] = False

        # przejście do Rezerwacji po zalogowaniu
        st.switch_page(rezerwacje_page)

