import streamlit as st
from supabase import create_client, Client
import pandas as pd
import plotly.express as px

# --- 1. KONFIGURACJA STRONY ---
st.set_page_config(page_title="Magazyn Pro", layout="wide")

# --- 2. POŁĄCZENIE Z SUPABASE ---
@st.cache_resource
def init_connection():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error("Błąd połączenia. Sprawdź plik secrets.toml")
        st.stop()

supabase = init_connection()

# --- 3. POBIERANIE DANYCH ---
@st.cache_data(ttl=600)
def fetch_data():
    try:
        # Pobieranie produktów z joinem kategorii
        p_res = supabase.table("produkty").select("*, kategorie(nazwa)").execute()
        k_res = supabase.table("kategorie").select("*").execute()
        return p_res.data, k_res.data
    except Exception as e:
        st.error(f"Błąd bazy danych: {e}")
        return [], []

def refresh():
    st.cache_data.clear()
    st.rerun()

# Załadowanie danych do DataFrame
prod_raw, kat_raw = fetch_data()
df_p = pd.DataFrame(prod_raw)
df_k = pd.DataFrame(kat_raw)

# --- 4. LOGIKA ANALITYCZNA ---
total_val = 0
low_stock_count = 0

if not df_p.empty:
    # Przygotowanie czytelnej nazwy kategorii
    if 'kategorie' in df_p.columns:
        df_p['kategoria_nazwa'] = df_p['kategorie'].apply(lambda x: x['nazwa'] if isinstance(x, dict) else "Brak")
    
    # Obliczenia
    df_p['wartosc_laczna'] = df_p['cena'] * df_p['liczba']
    total_val = df_p['wartosc_laczna'].sum()
    low_stock_df = df_p[df_p['liczba'] <= df_p['stan_minimalny']]
    low_stock_count = len(low_stock_df)

# --- 5. INTERFEJS UŻYTKOWNIKA ---
st.title("Zarządzanie Sklepem i Magazynem")

# Definicja zakładek (poprawiona linia, która generowała błąd)
t1, t2, t3 = st.tabs(["Magazyn", "Raporty", "Kategorie"])

# --- ZAKŁADKA 1: MAGAZYN ---
with t1:
    col_a, col_b = st.columns([1, 3])
    
    with col_a:
        st.subheader("Status")
        st.metric("Wartość towaru", f"{total_val:,.2f} PLN")
        st.metric("Niskie stany", low_stock_count)
        
        if low_stock_count > 0:
            st.warning("Produkty do dokupienia:")
            for _, r in low_stock_df.iterrows():
                st.caption(f"- {r['nazwa']} (szt: {r['liczba']})")

    with col_b:
        st.subheader("Lista i szybka edycja")
        if not df_p.empty:
            # Edytor tabeli
            edited = st.data_editor(
                df_p[['id', 'nazwa', 'kategoria_nazwa', 'cena', 'liczba', 'stan_minimalny']],
                use_container_width=True,
                hide_index=True,
                disabled=['id', 'kategoria_nazwa']
            )
            
            if st.button("Zapisz zmiany w tabeli"):
                for idx, row in edited.iterrows():
                    supabase.table("produkty").update({
                        "cena": row["cena"],
                        "liczba": row["liczba"],
                        "stan_minimalny": row["stan_minimalny"]
                    }).eq("id", row["id"]).execute()
                st.success("Zaktualizowano dane!")
                refresh()
        
        with st.expander("Dodaj nowy produkt"):
            if not df_k.empty:
                k_map = {row['nazwa']: row['id'] for _, row in df_k.iterrows()}
                with st.form("add
