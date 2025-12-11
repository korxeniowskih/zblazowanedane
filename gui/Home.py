import streamlit as st
from nav_pages import rezerwacje_page, bilety_page, login_page, register_page


st.title("🎬 KinoApp — Strona Główna")

if "logged" in st.session_state and st.session_state["logged"]:
    st.success(f"Witaj ponownie, **{st.session_state['user_name']}**!")

    st.write("Wybierz jedną z opcji poniżej:")

    col_res, col_tick, col_logout = st.columns(3)

    with col_res:
        if st.button("🎟️ Rezerwacje filmów"):
            st.switch_page(rezerwacje_page)
    
    with col_tick:
        if st.button("🎫 Moje Bilety"):
            st.switch_page(bilety_page)

    with col_logout:
        if st.button("🚪 Wyloguj"):
            st.session_state.clear()
            st.rerun()

else:
    st.info("Zaloguj się lub utwórz konto, aby korzystać z aplikacji.")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔐 Logowanie"):
            st.switch_page(login_page)

    with col2:
        if st.button("📝 Rejestracja"):
            st.switch_page(register_page)

