import streamlit as st
from supabase import create_client, Client
import pandas as pd
import plotly.express as px

# --- 1. KONFIGURACJA STRONY I POŁĄCZENIA ---
st.set_page_config(page_title="Magazyn Pro 🛒", layout="wide", page_icon="📦")

@st.cache_resource
def get_supabase_client():
    """Tworzy klienta Supabase i cache'uje go, aby nie tworzyć go przy każdym odświeżeniu."""
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error("Błąd konfiguracji Supabase. Sprawdź .streamlit/secrets.toml")
        st.stop()

supabase = get_supabase_client()

# --- 2. FUNKCJE DO POBIERANIA I ZAPISYWANIA DANYCH ---
@st.cache_data(ttl=600)  # Cache na 10 minut
def fetch_data():
    """Pobiera dane produktów i kategorii."""
    try:
        p = supabase.table("produkty").select("*, kategorie(nazwa)").execute()
        k = supabase.table("kategorie").select("*").execute()
        return p.data, k.data
    except Exception as e:
        st.error(f"Błąd pobierania: {e}")
        return [], []

def clear_cache_and_rerun():
    """Czyści cache i odświeża stronę."""
    st.cache_data.clear()
    st.rerun()

# Pobranie danych
prod_raw, kat_raw = fetch_data()
df_p = pd.DataFrame(prod_raw)
df_k = pd.DataFrame(kat_raw)

# --- 3. LOGIKA ANALITYCZNA ---
if not df_p.empty:
    # Mapowanie nazw kategorii
    if 'kategorie' in df_p.columns:
        df_p['kategoria_nazwa'] = df_p['kategorie'].apply(lambda x: x['nazwa'] if isinstance(x, dict) else "Brak")
    
    # Obliczenia finansowe
    df_p['wartosc_razem'] = df_p['cena'] * df_p['liczba']
    total_value = df_p['wartosc_razem'].sum()
    low_stock_df = df_p[df_p['liczba'] <= df_p['stan_minimalny']]

# --- 4. INTERFEJS UŻYTKOWNIKA (UI) ---
st.title("System Zarządzania Magazynem 🛒")

tab1, tab2, tab3 = st.tabs(["📦 Magazyn i Edycja", "📊 Rap
