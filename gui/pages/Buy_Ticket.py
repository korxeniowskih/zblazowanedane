import streamlit as st
import psycopg2
import pandas as pd
from psycopg2 import sql
from datetime import datetime, timedelta

# --- Konfiguracja połączenia z bazą danych ---
DB_CONFIG = {
    "dbname": "kino",
    "user": "admin",
    "password": "admin",
    "host": "db",
    "port": "5432"
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

# --- Funkcje bazy danych (bez zmian) ---
def fetch_data(query, params=None):
    """Pobiera dane z bazy i zwraca jako DataFrame."""
    try:
        conn = get_connection()
        df = pd.read_sql(query, conn, params=params)
        conn.close()
        return df
    except psycopg2.Error as e:
        st.error(f"❌ Błąd bazy danych podczas pobierania danych: {e}")
        return pd.DataFrame()

def execute_transaction(screening_id: int, seat_id: int, price_cents: int, customer_id: int):
    """Wykonuje transakcję zakupu biletu (Rezerwacja -> Płatność -> Bilet)."""
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        # 1. Sprawdzenie, czy miejsce jest na pewno wolne (ponowne sprawdzenie)
        cur.execute(
            """
            SELECT status FROM view_seat_status 
            WHERE screening_id = %s AND seat_id = %s
            """, 
            (screening_id, seat_id)
        )
        current_status = cur.fetchone()
        if current_status and current_status[0] != 'free':
            st.warning(f"Miejsce jest już {current_status[0]}. Spróbuj ponownie.")
            return False

        # 2. Utworzenie rezerwacji
        cur.execute(
            sql.SQL("""
                INSERT INTO reservations (customer_id, screening_id, expires_at)
                VALUES (%s, %s, %s)
                RETURNING id;
            """),
            (customer_id, screening_id, datetime.now() + timedelta(minutes=5))
        )
        reservation_id = cur.fetchone()[0]

        # 3. Dodanie miejsc do rezerwacji
        cur.execute(
            sql.SQL("""
                INSERT INTO reservation_seats (reservation_id, seat_id, price_cents)
                VALUES (%s, %s, %s);
            """),
            (reservation_id, seat_id, price_cents)
        )

        # 4. Finalizacja transakcji (PŁATNOŚĆ)
        cur.execute(
            sql.SQL("""
                UPDATE reservations SET status = 'paid' WHERE id = %s;
            """),
            (reservation_id,)
        )

        conn.commit()
        return True
        
    except psycopg2.IntegrityError:
        st.error("❌ To miejsce zostało właśnie zajęte. Odśwież widok i spróbuj ponownie.")
        if conn: conn.rollback()
        return False
    except psycopg2.Error as e:
        st.error(f"❌ Błąd bazy danych: {e}")
        if conn: conn.rollback()
        return False
    finally:
        if conn: conn.close()

# --- Interfejs Streamlit ---

# --- KONTROLA SESJI I INICJALIZACJA ---
if "user_id" not in st.session_state:
    st.session_state["user_id"] = None
if "logged" not in st.session_state:
    st.session_state["logged"] = False

# --- GLOBALNA LOGIKA SIDEBAR I WYLOGOWANIE ---
if "logged" in st.session_state and st.session_state["logged"]:
    with st.sidebar:
        st.success(f"Zalogowano jako: {st.session_state['user_name']}")
        if st.button("Wyloguj"):
            del st.session_state["logged"]
            del st.session_state["user_id"]
            del st.session_state["user_name"]
            st.switch_page("Login.py") # Przekierowanie do Login.py po wylogowaniu

st.title("🎫 Zakup Biletu")

# Kontrola dostępu
if not st.session_state["logged"] or st.session_state["user_id"] is None:
    st.warning("Musisz być zalogowany, aby kupić bilet.")
    st.page_link("Login.py", label="Przejdź do strony Logowanie")
    st.stop()
else:
    # Użycie ID klienta po zalogowaniu
    customer_id = st.session_state["user_id"]
    # Usunięto st.sidebar.success, zastąpione przez globalną logikę na górze

# ---------------------------------------------
# --- Główna Logika Zakupu ---

st.subheader("Wybór Seansu")

df_screenings = fetch_data(
    "SELECT * FROM view_screenings_with_movie WHERE start_time > NOW() ORDER BY movie_title, start_time"
)

if df_screenings.empty:
    st.info("Brak nadchodzących seansów.")
else:
    options = df_screenings.apply(
        lambda row: f"{row['movie_title']} ({row['start_time'].strftime('%Y-%m-%d %H:%M')}) w {row['hall_name']} | Cena: {row['base_price_cents'] / 100:.2f} PLN",
        axis=1
    )
    selected_option = st.selectbox("Wybierz seans:", options)
    
    if selected_option:
        selected_screening = df_screenings.loc[df_screenings.apply(
            lambda row: f"{row['movie_title']} ({row['start_time'].strftime('%Y-%m-%d %H:%M')}) w {row['hall_name']} | Cena: {row['base_price_cents'] / 100:.2f} PLN",
            axis=1
        ) == selected_option].iloc[0]

        # RZUTOWANIE NA INT: Usuwa problem z numpy.int64
        screening_id = int(selected_screening['screening_id'])
        price_cents = int(selected_screening['base_price_cents'])

        st.subheader(f"Wybrano: {selected_screening['movie_title']} w {selected_screening['hall_name']}")
        st.write(f"Cena biletu: **{price_cents / 100:.2f} PLN**")

        
        # --- Krok 2: Wybór Miejsca ---
        df_seats = fetch_data(
            f"""
            SELECT seat_id, row_label, seat_number, status
            FROM view_seat_status
            WHERE screening_id = {screening_id}
            ORDER BY row_label, seat_number
            """
        )
        
        if not df_seats.empty:
            free_seats = df_seats[df_seats['status'] == 'free']
            
            if free_seats.empty:
                st.warning("Brak wolnych miejsc na ten seans.")
            else:
                seat_options = free_seats.apply(
                    lambda row: f"Rząd {row['row_label']}, Miejsce {row['seat_number']}",
                    axis=1
                )
                
                selected_seat_label = st.selectbox("Wybierz wolne miejsce:", seat_options)
                
                if selected_seat_label:
                    # Mapowanie wybranej etykiety z powrotem na ID miejsca
                    selected_seat = free_seats.loc[free_seats.apply(
                        lambda row: f"Rząd {row['row_label']}, Miejsce {row['seat_number']}",
                        axis=1
                    ) == selected_seat_label].iloc[0]
                    
                    # RZUTOWANIE NA INT: Usuwa problem z numpy.int64
                    seat_id = int(selected_seat['seat_id'])

                    st.markdown(f"Wybrane miejsce: **{selected_seat_label}**")
                    
                    # --- Krok 3: Przycisk Zakupu ---
                    if st.button("Kup Bilet Teraz"):
                        with st.spinner('Przetwarzanie transakcji...'):
                            # Przekazujemy wszystkie zmienne jako standardowe int
                            if execute_transaction(screening_id, seat_id, price_cents, customer_id):
                                st.success("✅ Sukces! Bilet został zakupiony i wygenerowany. Zobacz go w sekcji 'Moje Bilety'.")
                                # Przekierowanie do strony z biletami po zakupie
                                st.switch_page("pages/Moje_Bilety.py")
                            else:
                                st.error("❌ Transakcja nie powiodła się.")

        else:
            st.error("Błąd ładowania statusu miejsc.")