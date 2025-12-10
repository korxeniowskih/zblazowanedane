import streamlit as st
from nav_pages import (
    home_page,
    login_page,
    register_page,
    rezerwacje_page,
    bilety_page,
    buy_ticket_page,
    admin_page,
)

st.set_page_config(page_title="KinoApp", page_icon="🎬", layout="wide")

# --- Domyślne wartości sesji ---
if "logged" not in st.session_state:
    st.session_state["logged"] = False

if "user_name" not in st.session_state:
    st.session_state["user_name"] = "Gość"

if "is_admin" not in st.session_state:
    st.session_state["is_admin"] = False  # w przyszłości możesz ustawiać to z bazy


logged   = st.session_state["logged"]
is_admin = st.session_state["is_admin"]

# --- Dynamiczna lista stron ---
if not logged:
    pages = {
        "KinoApp": [home_page],
        "Konto": [login_page, register_page],
    }
else:
    pages = {
        "KinoApp": [home_page],
        "Rezerwacje": [rezerwacje_page, bilety_page, buy_ticket_page],
    }
    if is_admin:
        pages["Administracja"] = [admin_page]

pg = st.navigation(pages, position="sidebar")  # lub "top"
pg.run()

