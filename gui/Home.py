import streamlit as st

st.set_page_config(page_title="KinoApp", page_icon="🎬", layout="wide") # Dodano layout="wide" i ikonę

st.title("🎬 KinoApp — Strona Główna")

# Jeśli użytkownik jest zalogowany, witamy go
if "logged" in st.session_state and st.session_state["logged"]:
    st.success(f"Witaj ponownie, **{st.session_state['user_name']}**!")

    st.write("Wybierz jedną z opcji poniżej:")

    col_res, col_tick, col_logout = st.columns(3) # Nowy układ kolumn

    with col_res:
        # Przejście do rezerwacji
        if st.button("🎟️ Rezerwacje filmów"):
            st.switch_page("pages/Rezerwacje.py")
    
    with col_tick:
        # Przejście do Moje Bilety
        if st.button("🎫 Moje Bilety"):
            st.switch_page("pages/Moje_bilety.py")

    with col_logout:
        if st.button("🚪 Wyloguj"):
            st.session_state.clear()
            st.rerun()

else:
    st.info("Zaloguj się lub utwórz konto, aby korzystać z aplikacji.")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔐 Logowanie"):
            st.switch_page("pages/Login.py")

    with col2:
        if st.button("📝 Rejestracja"):
            st.switch_page("pages/Register.py")