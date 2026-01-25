import streamlit as st
from supabase import create_client, Client
import pandas as pd

# 1. Konfiguracja połączenia
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Błąd połączenia z Supabase. Sprawdź secrets.toml.")
    st.stop()

st.set_page_config(page_title="Magazyn Pro", layout="wide")

# --- FUNKCJE DANYCH ---
def fetch_data():
    try:
        p = supabase.table("produkty").select("*, kategorie(nazwa)").execute()
        k = supabase.table("kategorie").select("*").execute()
        return p.data, k.data
    except Exception as e:
        st.error(f"Błąd danych: {e}")
        return [], []

prod_raw, kat_raw = fetch_data()

st.title("Zarządzanie Sklepem 🛒")

tab1, tab2, tab3 = st.tabs(["📦 Produkty", "📊 Analiza Magazynu", "📂 Kategorie"])

# --- TAB 1: PRODUKTY ---
with tab1:
    st.header("Lista Produktów")
    if prod_raw:
        df_p = pd.DataFrame(prod_raw)
        if 'kategorie' in df_p.columns:
            df_p['kategoria_nazwa'] = df_p['kategorie'].apply(lambda x: x['nazwa'] if isinstance(x, dict) else "Brak")
        
        cols = ['id', 'nazwa', 'kategoria_nazwa', 'liczba', 'stan_minimalny', 'cena']
        existing = [c for c in cols if c in df_p.columns]
        st.dataframe(df_p[existing], use_container_width=True, hide_index=True)
    
    with st.expander("➕ Dodaj produkt"):
        if kat_raw:
            kat_dict = {k['nazwa']: k['id'] for k in kat_raw}
            with st.form("add_p"):
                n = st.text_input("Nazwa")
                k_n = st.selectbox("Kategoria", options=list(kat_dict.keys()))
                c1, c2 = st.columns(2)
                price = c1.number_input("Cena", min_value=0.0)
                qty = c2.number_input("Ilość", min_value=0)
                s_min = st.number_input("Stan min.", min_value=0)
                if st.form_submit_button("Zapisz"):
                    supabase.table("produkty").insert({
                        "nazwa": n, "kategoria_id": kat_dict[k_n],
                        "cena": price, "liczba": qty, "stan_minimalny": s_min
                    }).execute()
                    st.rerun()

# --- TAB 2: ANALIZA ---
with tab2:
    st.header("Statystyki ogólne")
    if prod_raw:
        df_a = pd.DataFrame(prod_raw)
        val = (df_a.get('cena', 0) * df_a.get('liczba', 0)).sum()
        st.metric("Całkowita wartość", f"{val:,.2f} PLN")

# --- TAB 3: KATEGORIE + PODSUMOWANIE ---
with tab3:
    st.header("Zarządzanie Kategoriami")
    
    # --- NOWA SEKCJA: PODSUMOWANIE PRODUKTÓW W KATEGORIACH ---
    if kat_raw and prod_raw:
        st.subheader("📊 Podsumowanie produktów w kategoriach")
        
        df_p_sub = pd.DataFrame(prod_raw)
        df_k_sub = pd.DataFrame(kat_raw)
        
        # Przygotowanie danych do agregacji
        df_p_sub['wartosc'] = df_p_sub.get('cena', 0) * df_p_sub.get('liczba', 0)
        
        # Agregacja po kategoria_id
        summary = df_p_sub.groupby('kategoria_id').agg(
            liczba_produktow=('id', 'count'),
            suma_sztuk=('liczba', 'sum'),
            laczna_wartosc=('wartosc', 'sum')
        ).reset_index()
        
        # Połączenie z nazwą kategorii
        full_summary = pd.merge(df_k_sub[['id', 'nazwa']], summary, left_on='id', right_on='kategoria_id', how='left').fillna(0)
        
        # Wyświetlenie tabeli podsumowującej
        st.table(full_summary[['nazwa', 'liczba_produktow', 'suma_sztuk', 'laczna_wartosc']].rename(columns={
            'nazwa': 'Kategoria',
            'liczba_produktow': 'Ilość typów produktów',
            'suma_sztuk': 'Łącznie sztuk',
            'laczna_wartosc': 'Wartość (PLN)'
        }))
        st.divider()

    # Formularz dodawania kategorii
    with st.expander("➕ Dodaj nową kategorię"):
        with st.form("add_c"):
            name = st.text_input("Nazwa kategorii")
            if st.form_submit_button("Dodaj"):
                if name:
                    supabase.table("kategorie").insert({"nazwa": name}).execute()
                    st.rerun()

    # Lista wszystkich kategorii z opcją usuwania
    if kat_raw:
        st.subheader("Lista kategorii")
        df_kat_list = pd.DataFrame(kat_raw)
        st.dataframe(df_kat_list[['id', 'nazwa']], use_container_width=True)
        
        to_del = st.selectbox("Usuń kategorię", options=kat_raw, format_func=lambda x: x['nazwa'])
        if st.button("Usuń kategorię", type="primary"):
            try:
                supabase.table("kategorie").delete().eq("id", to_del['id']).execute()
                st.rerun()
            except:
                st.error("Błąd: Kategoria może zawierać produkty. Usuń je najpierw.")
