import streamlit as st
from supabase import create_client, Client
import pandas as pd
import plotly.express as px

# --- 1. KONFIGURACJA STRONY ---
st.set_page_config(page_title="Magazyn Pro", layout="wide")

# --- 2. POLACZENIE Z SUPABASE ---
@st.cache_resource
def init_connection():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error("Blad konfiguracji secrets.toml")
        st.stop()

supabase = init_connection()

# --- 3. FUNKCJE POBIERANIA DANYCH ---
@st.cache_data(ttl=600)
def fetch_data():
    try:
        # Pobieranie produktow wraz z nazwa kategorii
        p_res = supabase.table("produkty").select("*, kategorie(nazwa)").execute()
        k_res = supabase.table("kategorie").select("*").execute()
        return p_res.data, k_res.data
    except Exception as e:
        return [], []

def refresh():
    st.cache_data.clear()
    st.rerun()

# Zaladowanie danych do pamieci aplikacji
prod_raw, kat_raw = fetch_data()
df_p = pd.DataFrame(prod_raw)
df_k = pd.DataFrame(kat_raw)

# --- 4. LOGIKA ANALITYCZNA ---
total_val = 0
if not df_p.empty:
    # Mapowanie relacji kategorii
    if "kategorie" in df_p.columns:
        df_p["kategoria_nazwa"] = df_p["kategorie"].apply(lambda x: x["nazwa"] if isinstance(x, dict) else "Brak")
    
    # Obliczanie wartosci magazynu
    df_p["wartosc_suma"] = df_p["cena"] * df_p["liczba"]
    total_val = df_p["wartosc_suma"].sum()

# --- 5. INTERFEJS UZYTKOWNIKA ---
st.title("System Zarzadzania Magazynem i Sklepem")

# Zakladki bez znakow specjalnych dla bezpieczenstwa kodu
tab1, tab2, tab3 = st.tabs(["Magazyn", "Raporty", "Kategorie"])

# --- TAB 1: MAGAZYN I EDYCJA ---
with tab1:
    col_a, col_b = st.columns([1, 3])
    
    with col_a:
        st.subheader("Podsumowanie")
        st.metric("Wartosc towaru", f"{total_val:,.2f} PLN")
        
        if not df_p.empty:
            low_stock = df_p[df_p["liczba"] <= df_p["stan_minimalny"]]
            if not low_stock.empty:
                st.warning(f"Braki towaru: {len(low_stock)}")
                for _, r in low_stock.iterrows():
                    st.caption(f"- {r['nazwa']} (Stan: {r['liczba']})")
            else:
                st.success("Stany magazynowe OK")

    with col_b:
        st.subheader("Inwentaryzacja")
        if not df_p.empty:
            # Interaktywny edytor tabeli
            edited = st.data_editor(
                df_p[["id", "nazwa", "kategoria_nazwa", "cena", "liczba", "stan_minimalny"]],
                use_container_width=True, 
                hide_index=True,
                disabled=["id", "kategoria_nazwa"]
            )
            
            if st.button("Zapisz zmiany zbiorczo"):
                for _, row in edited.iterrows():
                    supabase.table("produkty").update({
