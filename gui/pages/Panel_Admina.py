import streamlit as st
import psycopg2
import pandas as pd
from datetime import datetime, timedelta
from psycopg2 import sql

# --- KONFIGURACJA BAZY DANYCH (ADMIN) ---
# UWAGA: Używamy roli 'admin' z pełnymi uprawnieniami (Superuser)
# zgodnie z docker-compose.yml, co jest wymagane do operacji DELETE/INSERT/UPDATE na wszystkich tabelach.
DB_CONFIG_ADMIN = {
    "dbname": "kino",
    "user": "admin",
    "password": "admin", 
    "host": "db",
    "port": "5432"
}

def get_admin_connection():
    """Zwraca połączenie z uprawnieniami ADMIN."""
    return psycopg2.connect(**DB_CONFIG_ADMIN)

# --- Funkcje Bazy Danych ---

def fetch_data(query, params=None):
    """Pobiera dane do wyświetlania."""
    conn = get_admin_connection()
    try:
        df = pd.read_sql(query, conn, params=params)
        return df
    except Exception as e:
        st.error(f"❌ Błąd ładowania danych: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def execute_admin_query(query, params=None):
    """Wykonuje operacje modyfikacji (INSERT/DELETE) za pomocą roli ADMIN."""
    conn = None
    try:
        conn = get_admin_connection()
        cur = conn.cursor()
        cur.execute(query, params)
        conn.commit()
        cur.close()
        return True
    except psycopg2.Error as e:
        st.error(f"❌ Błąd krytyczny bazy danych: {e}")
        if conn: conn.rollback()
        return False
    finally:
        if conn: conn.close()

# ---------------------------------------------
# --- KONTROLA SESJI I DOSTĘPU ---
# ---------------------------------------------

# Prosta weryfikacja logowania
if "logged" not in st.session_state or not st.session_state["logged"] or st.session_state['user_name'] != "admin" :
    st.error("Dostęp tylko dla admina.")
    st.stop()
    
# --- GLOBALNA LOGIKA SIDEBAR ---
if st.session_state["logged"]:
    with st.sidebar:
        st.success(f"Zalogowano jako: {st.session_state['user_name']}")
        if st.button("Wyloguj"):
            del st.session_state["logged"]
            del st.session_state["user_id"]
            del st.session_state["user_name"]
            st.switch_page("Login.py")

st.title("🛡️ Panel Administracyjny")
st.warning("Ta strona używa uprawnień superużytkownika (admin).")

# ---------------------------------------------
# --- A. DODAWANIE NOWEGO SEANSU ---
# ---------------------------------------------
st.header("1. Dodaj Nowy Seans")

col1, col2 = st.columns(2)
with col1:
    movies_df = fetch_data("SELECT id, title FROM movies ORDER BY title")
    halls_df = fetch_data("SELECT id, name, capacity FROM halls ORDER BY name")
    
    movie_options = {row['title']: row['id'] for _, row in movies_df.iterrows()}
    hall_options = {row['name']: row['id'] for _, row in halls_df.iterrows()}
    
    selected_movie_title = st.selectbox("Film:", list(movie_options.keys()))
    selected_hall_name = st.selectbox("Sala:", list(hall_options.keys()))

    movie_id = movie_options.get(selected_movie_title)
    hall_id = hall_options.get(selected_hall_name)

with col2:
    start_date = st.date_input("Data rozpoczęcia:", datetime.now().date())
    start_time_obj = st.time_input("Godzina rozpoczęcia:", datetime.now().time())
    
    # Złożenie daty i godziny
    start_time = datetime.combine(start_date, start_time_obj)
    
    duration_min = st.number_input("Czas trwania (min):", min_value=10, value=120)
    end_time = start_time + timedelta(minutes=duration_min)
    
    base_price = st.number_input("Cena bazowa (PLN):", min_value=0.01, value=25.00)
    base_price_cents = int(base_price * 100)

st.write(f"Seans zakończy się o: {end_time.strftime('%Y-%m-%d %H:%M')}")

if st.button("Zaplanuj Seans", key="schedule_btn"):
    # Walidacja odbywa się w bazie za pomocą triggera validate_screening_overlap
    query = """
    INSERT INTO screenings (movie_id, hall_id, start_time, end_time, language, is_3d, base_price_cents, status)
    VALUES (%s, %s, %s, %s, 'original', FALSE, %s, 'scheduled')
    """
    params = (movie_id, hall_id, start_time, end_time, base_price_cents)
    
    if execute_admin_query(query, params):
        st.success(f"✅ Seans '{selected_movie_title}' w Sali {selected_hall_name} został dodany.")


st.markdown("---")
# ---------------------------------------------
# --- B. ZARZĄDZANIE UŻYTKOWNIKAMI I BILETAMI ---
# ---------------------------------------------
st.header("2. Zarządzanie Klientami i Biletami")

customers_data = fetch_data("SELECT id, first_name, last_name, email FROM customers ORDER BY id")
if customers_data.empty:
    st.info("Brak zarejestrowanych klientów.")
    # St.stop() jest niepotrzebne, bo chcemy umożliwić dodanie seansu nawet bez klientów.

customers_options = {f"{row['email']} ({row['first_name']} {row['last_name']})": row['id'] 
                     for _, row in customers_data.iterrows()}

selected_customer_email = st.selectbox("Wybierz klienta do zarządzania:", list(customers_options.keys()))
customer_id_to_manage = customers_options.get(selected_customer_email)

if customer_id_to_manage is not None:
    
    st.subheader("Bilety Klienta")
    # Pobierz bilety klienta do wyświetlenia i zarządzania
    tickets_query = f"""
        SELECT t.id, m.title, h.name AS hall, s.start_time, t.status 
        FROM tickets t
        JOIN screenings s ON t.screening_id = s.id
        JOIN movies m ON s.movie_id = m.id
        JOIN halls h ON s.hall_id = h.id
        WHERE t.customer_id = {customer_id_to_manage}
        ORDER BY s.start_time DESC
    """
    tickets_df = fetch_data(tickets_query)

    if not tickets_df.empty:
        st.dataframe(tickets_df, hide_index=True)

        ticket_ids = tickets_df['id'].tolist()
        
        st.subheader("Anulowanie Biletu")
        ticket_id_to_cancel = st.selectbox("Wybierz ID biletu do anulowania:", ticket_ids, key="cancel_select")

        if st.button("Anuluj Wybrany Bilet", key="cancel_btn"):
            cancel_query = "UPDATE tickets SET status = 'cancelled' WHERE id = %s"
            if execute_admin_query(cancel_query, (ticket_id_to_cancel,)):
                st.success(f"✅ Bilet ID {ticket_id_to_cancel} został anulowany.")
                st.rerun()
    else:
        st.info("Klient nie ma obecnie żadnych biletów.")

    st.markdown("---")
    st.subheader("Usuń Konto Klienta")
    st.warning("Ta operacja usuwa klienta i WSZYSTKIE powiązane rekordy. Jest NIEODWRACALNA!")

    if st.button(f"USUŃ KLIENTA: {selected_customer_email}", key="delete_customer"):
        
        confirm = st.text_input(f"Potwierdź usunięcie, wpisując 'USUŃ {customer_id_to_manage}':")
        
        if confirm == f"USUŃ {customer_id_to_manage}":
            # Usunięcie powiązanych rekordów (od najbardziej zależnych)
            delete_queries = [
                # 1. Usuń miejsca w rezerwacji
                "DELETE FROM reservation_seats WHERE reservation_id IN (SELECT id FROM reservations WHERE customer_id = %s)",
                # 2. Usuń bilety (jeśli nie mają referencji do rezerwacji)
                "DELETE FROM tickets WHERE customer_id = %s",
                # 3. Usuń rezerwacje
                "DELETE FROM reservations WHERE customer_id = %s",
                # 4. Usuń klienta
                "DELETE FROM customers WHERE id = %s"
            ]
            
            success = True
            for q in delete_queries:
                if not execute_admin_query(q, (customer_id_to_manage,)):
                    success = False
                    break

            if success:
                st.success(f"✅ Klient ID {customer_id_to_manage} i wszystkie powiązane dane zostały trwale usunięte.")
                st.rerun()
            else:
                st.error("Wystąpił błąd podczas usuwania powiązanych rekordów. Sprawdź logi bazy.")