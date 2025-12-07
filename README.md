# 🚀 KINO-APP: Dokumentacja Projektu i Instrukcja Uruchomienia

Projekt Kinowy opiera się na kontenerach Docker i wykorzystuje architekturę Streamlit (interfejs użytkownika) oraz PostgreSQL (baza danych).

## 1. Wymagania wstępne ⚙️

Aby uruchomić projekt lokalnie, potrzebne są:

- **Docker**
- **Docker Compose**

---

## 2. Instrukcja Uruchomienia 💾

Instrukcja zakłada, że znajdujesz się w głównym katalogu projektu (`kino-projekt/`).


### A. Konfiguracja i Inicjalizacja (Pierwsze Uruchomienie)

**Uwaga:** Wprowadzono zmiany w schemacie SQL oraz uprawnieniach, dlatego wymagane jest wyczyszczenie wcześniejszych danych, aby baza poprawnie załadowała nowe definicje i widoki.

1. **Zatrzymanie i usunięcie starych kontenerów oraz wolumenów danych:**
   ```bash
   docker-compose down -v
   ```

2. **Ręczne usunięcie folderu danych PostgreSQL (jeśli istnieje):**
   ```bash
   # Windows (PowerShell)
   Remove-Item -Recurse -Force data

   # Linux / macOS
   rm -rf data
   ```

3. **Budowanie i uruchomienie projektu:**
   ```bash
   docker-compose up --build
   ```

### B. Regularne Uruchomienie

Jeśli projekt został już skonfigurowany wcześniej:

```bash
docker-compose up
```

### C. Dostęp do Aplikacji

Po udanym uruchomieniu otwórz w przeglądarce:

- Panel użytkownika (Streamlit): **http://localhost:8501**

---

## 3. Architektura i Uprawnienia Bazy Danych 🛡️

Projekt korzysta z dwóch usług Docker oraz dwóch głównych ról PostgreSQL.

### A. Usługi Docker

| Usługa | Technologia    | Opis |
|--------|----------------|------|
| db     | PostgreSQL 16  | Główna baza danych. Schemat ładowany z `database/baza.sql`. |
| gui    | Streamlit      | Aplikacja front‑end. |

### B. Role Systemowe PostgreSQL

> Dane logowania są zapisane bezpośrednio w plikach `.py`  
> - użytkownik: **web / web**  
> - administrator: **admin / admin**

| Rola PostgreSQL | Poświadczenia | Zakres uprawnień | Użycie w aplikacji |
|------------------|---------------|------------------|--------------------|
| web              | web / web     | Ograniczone — INSERT/UPDATE na tabelach transakcyjnych (customers, reservations, reservation_seats). SELECT na wszystkich widokach (repertuar, bilety itd.). | Wszystkie strony klienta (Login, Buy_Ticket, Rezerwacje). |
| admin            | admin / admin | Pełny dostęp (superuser). | Panel administracyjny (`Panel_Admina.py`). |

---

## 4. Narzędzia Konsolowe (psql)

Aby połączyć się z bazą danych w trybie konsolowym (np. w celach diagnostycznych), użyj konta **admin**:

```bash
docker exec -it kino psql -U admin kino
```

# 🧱 Warunki integralnościowe, logika bazy danych i zasady bezpieczeństwa

## 🌐 Informacja o wersji demonstracyjnej aplikacji webowej

Warstwa webowa aplikacji została przygotowana **jako interfejs poglądowy** — jej celem jest wizualizacja działania systemu bazodanowego oraz prezentacja operacji wykonywanych na danych.  
Ponieważ projekt koncentruje się przede wszystkim na **architekturze bazy danych, integralności danych i warstwie SQL**, aplikacja webowa **nie była projektowana z pełnym naciskiem na bezpieczeństwo klasy produkcyjnej**.

Oznacza to m.in.:

- brak zaawansowanych mechanizmów ochrony sesji i tokenów,
- brak kompleksowej walidacji wejścia po stronie frontend/backend,
- uproszczone podejście do obsługi autoryzacji,
- uproszczoną architekturę typową dla projektów dydaktycznych.

Bezpieczeństwo systemu jest zatem **egzekwowane głównie w samej bazie danych**, poprzez role, uprawnienia, triggery i funkcje.

---

# ## 🧱 Warunki integralnościowe (Constraints)

System korzysta z wielu typów ograniczeń integralnościowych, które zapewniają spójność i poprawność danych.

### **1. Klucze główne (PRIMARY KEY)**  
Każda tabela posiada klucz główny — np. customers(id), movies(id), screenings(id), tickets(id).

### **2. Klucze obce (FOREIGN KEY)**  
Powiązania pomiędzy tabelami zapobiegają istnieniu danych „oderwanych”, np.:

- reservations.customer_id → customers.id  
- reservations.screening_id → screenings.id  
- reservation_seats.seat_id → seats.id  
- tickets.screening_id → screenings.id  
- screenings.movie_id → movies.id  

### **3. Ograniczenia unikalności (UNIQUE)**  
Przykładowe pola unikalne:

- customers.email  
- employees.email  
- halls.name  
- (hall_id, row_label, seat_number) – unikatowe miejsce

### **4. Ograniczenia wartości (CHECK / domyślne)**  
Przykłady:

- statusy domyślne (`pending`, `scheduled`, `sold`)  
- wartości boolean w polach konfiguracyjnych sal lub statusach obiektów

### **5. Integralność czasowa seansów**  
Zapewniana przez trigger blokujący **nakładające się seanse w tej samej sali**.

---

# ## 🔧 Warstwa dostępu do danych (Funkcje, widoki, triggery)

System implementuje część logiki biznesowej bezpośrednio w bazie.

## ### 1. Funkcje (FUNCTIONS)

### **create_tickets_after_payment()**  
Automatycznie tworzy bilety po zmianie statusu rezerwacji na „paid”.

### **expire_reservations()**  
Wygasza rezerwacje zaległe, zmieniając ich status na „expired”.

### **validate_screening_overlap()**  
Weryfikuje, czy seans nie nakłada się na inny seans w tej samej sali.

---

## ### 2. Triggery (TRIGGERS)

### **trg_create_tickets_after_payment**  
Wywoływany po aktualizacji rezerwacji – generuje bilety w tabeli tickets.

### **trg_validate_screening_overlap**  
Uruchamiany przed wstawieniem/aktualizacją seansu – zapobiega konfliktowi czasowemu.

---

## ### 3. Widoki (VIEWS)

Widoki udostępniają przetworzone dane dla aplikacji, bez konieczności wykonywania skomplikowanych zapytań.

### **view_customer_tickets**  
Zawiera informacje o biletach klienta wraz z filmem, salą i miejscem.

### **view_reservations_details**  
Łączy dane rezerwacji z klientem, filmem i salą.

### **view_screenings_with_movie**  
Lista seansów wraz z filmem, gatunkiem i salą.

### **view_employee_shifts**  
Zestawienie zmian pracowniczych.

### **view_seat_status**  
Określa status miejsca (free / reserved / taken) dla każdego seansu.

---

# ## 🔐 Uprawnienia i zasady bezpieczeństwa

Aplikacja korzysta z dwóch ról w PostgreSQL:

---

## ### 1. Rola **admin**
- pełny dostęp (superuser),
- właściciel całego schematu,
- używana tylko w panelu administracyjnym.

---

## ### 2. Rola **web**
Uprawnienia ograniczone do działań, które może wykonywać klient aplikacji.

### Uprawnienia roli web:

| Typ obiektu | Uprawnienia |
|-------------|-------------|
| Tabele danych | SELECT |
| Tabele transakcyjne | INSERT/UPDATE tam, gdzie wymagane |
| Sekwencje | SELECT + USAGE |
| Widoki | SELECT |

Przykłady:
- GRANT SELECT, INSERT ON customers TO web  
- GRANT SELECT, INSERT, UPDATE ON reservations TO web  
- GRANT SELECT ON view_* TO web  

---

# ## 🛡️ Zasady bezpieczeństwa (Realizowane w warstwie bazy)

1. Ograniczona rola web – tylko niezbędne operacje.  
2. Logika biznesowa wymuszona przez triggery i funkcje.  
3. Brak możliwości modyfikacji danych administracyjnych przez użytkownika.  
4. Automatyczne walidacje (np. konflikt seansów).  
5. Widoki jako bezpieczna warstwa odczytowa dla aplikacji.

---

# 📌 Uwagi końcowe

Ten zestaw mechanizmów integralnościowych i bezpieczeństwa stoi w centrum projektu –  
aplikacja webowa ma rolę **prezentacyjną**, natomiast **prawdziwe bezpieczeństwo i spójność systemu zapewnia baza danych**.
