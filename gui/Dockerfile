FROM python:3.10-slim

# Instalacja zależności systemowych
RUN apt-get update && apt-get install -y libpq-dev gcc

# Ustawiamy katalog pracy
WORKDIR /app

# Kopiujemy wymagania
COPY requirements.txt /app/

# Instalujemy biblioteki (streamlit, psycopg2 itd.)
RUN pip install --no-cache-dir -r requirements.txt

# Kopiujemy całą aplikację Streamlit
COPY . /app/

# Domyślna komenda uruchamiająca Streamlit
CMD ["python", "-m", "streamlit", "run", "Home.py", "--server.port=8501", "--server.address=0.0.0.0"]
