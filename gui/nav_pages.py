import streamlit as st

# Plik /app/nav_pages.py

home_page        = st.Page("Home.py",              title="Strona główna", icon="🎬")

login_page       = st.Page("pages/Login.py",       title="Logowanie",     icon="🔐")
register_page    = st.Page("pages/Register.py",    title="Rejestracja",   icon="📝")

rezerwacje_page  = st.Page("pages/Rezerwacje.py",  title="Rezerwacje",    icon="🎟️")
bilety_page      = st.Page("pages/Moje_Bilety.py", title="Moje bilety",   icon="🎫")
buy_ticket_page  = st.Page("pages/Buy_Ticket.py",  title="Kup bilet",     icon="🛒")

admin_page       = st.Page("pages/Panel_Admina.py", title="Panel Admina", icon="🛠️")
