import streamlit as st
from supabase import create_client, Client
import pandas as pd

# 1. Konfiguracja połączenia z Supabase
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Błąd połączenia z Supabase. Sprawdź plik secrets.toml.")
    st.stop()

# Ustawienie szerokiego układu strony
st.set_page_config(page_title="Magazyn Pro 🛒", layout="wide")

# --- FUNKCJE POMOCNICZE ---
def fetch_data():
    """Pobiera dane produktów i kategorii z bazy."""
    try:
        # Pobieramy produkty z dołączoną nazwą kategorii (join)
        p = supabase.table("produkty").select("*, kategorie(nazwa)").execute()
        k = supabase.table("kategorie").select("*").execute()
        return p.data, k.data
    except Exception as e:
        st.error(f"Błąd pobierania danych: {e}")
        return [], []

# Pobranie danych na starcie aplikacji
prod_raw, kat_raw = fetch_data()

st.title("Zarządzanie Sklepem i Magazynem 🛒")

# --- STRUKTURA ZAKŁADEK ---
tab1, tab2 = st.tabs(["📦 Produkty i Analiza", "📂 Kategorie"])

# --- TAB 1: PRODUKTY I ANALIZA (UKŁAD PIONOWY PO LEWEJ) ---
with tab1:
    # Podział strony: Lewa kolumna (Analiza) - 1/4 szerokości, Prawa (Produkty) - 3/4 szerokości
    col_left, col_right = st.columns([1, 3], gap="large")

    # --- LEWA STRONA: ANALIZA (PIONOWO) ---
    with col_left:
        st.subheader("📊 Analiza")
        if prod_raw:
            df_a = pd.DataFrame(prod_raw)
            
            # Obliczenia (bezpieczne pobieranie kolumn)
            cena_col = df_a.get('cena', 0)
            liczba_col = df_a.get('liczba', 0)
            stan_min_col = df_a.get('stan_minimalny', 0)
            
            total_val = (cena_col * liczba_col).sum()
            low_stock = df_a[liczba_col <= stan_min_col]
            
            # Statystyki wyświetlane pionowo (jedna pod drugą)
            st.metric("Wartość towaru", f"{total_val:,.2f} PLN")
            st.metric("Asortyment", f"{len(df_a)} poz.")
            st.metric("Do uzupełnienia", len(low_stock))
            
            st.divider()
            
            # Alerty stanów minimalnych
            if not low_stock.empty:
                st.warning("⚠️ Brakujące towary:")
                for _, row in low_stock.iterrows():
                    st.caption(f"**{row['nazwa']}** (Stan: {row['liczba']})")
            else:
                st.success("Wszystkie stany OK ✅")
        else:
            st.info("Brak danych.")

    # --- PRAWA STRONA: LISTA PRODUKTÓW ---
    with col_right:
        st.subheader("📋 Lista Produktów")
        if prod_raw:
            df_p = pd.DataFrame(prod_raw)
            
            # Mapowanie nazwy kategorii dla czytelności
            if 'kategorie' in df_p.columns:
                df_p['kategoria_nazwa'] = df_p['kategorie'].apply(lambda x: x['nazwa'] if isinstance(x, dict) else "Brak")
            
            # Wybór kolumn do wyświetlenia
            cols_to_show = ['id', 'nazwa', 'kategoria_nazwa', 'liczba', 'stan_minimalny', 'cena', 'ocena']
            existing_cols = [c for c in cols_to_show if c in df_p.columns]
            
            st.dataframe(df_p[existing_cols], use_container_width=True, hide_index=True)
        else:
            st.info("Dodaj pierwszy produkt.")

        # Formularz dodawania produktów
        with st.expander("➕ Dodaj nowy produkt"):
            if kat_raw:
                kat_options = {item['nazwa']: item['id'] for item in kat_raw}
                with st.form("add_product"):
                    col1, col2 = st.columns(2)
                    p_name = col1.text_input("Nazwa produktu")
                    p_cat = col1.selectbox("Kategoria", options=list(kat_options.keys()))
                    p_price = col2.number_input("Cena (PLN)", min_value=0.0, step=0.01)
                    p_ocena = col2.number_input("Ocena", min_value=0.0, max_value=5.0, step=0.1)
                    
                    c3, c4 = st.columns(2)
                    p_qty = c3.number_input("Ilość sztuk", min_value=0, step=1)
                    p_min = c4.number_input("Stan minimalny", min_value=0, step=1)
                    
                    if st.form_submit_button("Dodaj do bazy"):
                        if p_name:
                            supabase.table("produkty").insert({
                                "nazwa": p_name, "kategoria_id": kat_options[p_cat],
                                "cena": p_price, "liczba": p_qty, 
                                "stan_minimalny": p_min, "ocena": p_ocena
                            }).execute()
                            st.rerun()
            else:
                st.error("Musisz najpierw dodać kategorię!")

# --- TAB 2: KATEGORIE I PODSUMOWANIE ---
with tab2:
    st.header("Zarządzanie Kategoriami")
    
    # 1. Podsumowanie produktów w kategoriach
    if kat_raw and prod_raw:
        st.subheader("📊 Podsumowanie ilościowe")
        df_p_sub = pd.DataFrame(prod_raw)
        df_k_sub = pd.DataFrame(kat_raw)
        
        # Wyliczenie wartości dla każdego produktu
        df_p_sub['wartosc'] = df_p_sub.get('cena', 0) * df_p_sub.get('liczba', 0)
        
        # Agregacja danych
        summary = df_p_sub.groupby('kategoria_id').agg(
            liczba_typów=('id', 'count'),
            razem_sztuk=('liczba', 'sum'),
            suma_wartosc=('wartosc', 'sum')
        ).reset_index()
        
        # Połączenie z nazwami kategorii
        full_sum = pd.merge(df_k_sub[['id', 'nazwa']], summary, left_on='id', right_on='kategoria_id', how='left').fillna(0)
        
        st.table(full_sum[['nazwa', 'liczba_typów', 'razem_sztuk', 'suma_wartosc']].rename(columns={
            'nazwa': 'Kategoria', 'liczba_typów': 'Rodzaje produktów',
            'razem_sztuk': 'Łącznie sztuk', 'suma_wartosc': 'Wartość (PLN)'
        }))

    # 2. Dodawanie kategorii
    with st.expander("➕ Dodaj nową kategorię"):
        with st.form("add_category"):
            new_cat_name = st.text_input("Nazwa kategorii")
            new_cat_desc = st.text_area("Opis")
            if st.form_submit_button("Zapisz kategorię"):
                if new_cat_name:
                    supabase.table("kategorie").insert({"nazwa": new_cat_name, "opis": new_cat_desc}).execute()
                    st.rerun()

    # 3. Usuwanie kategorii
    if kat_raw:
        st.divider()
        st.subheader("🗑️ Usuwanie")
        to_del = st.selectbox("Wybierz kategorię do usunięcia", options=kat_raw, format_func=lambda x: x['nazwa'])
        if st.button("Usuń kategorię", type="primary"):
            try:
                supabase.table("kategorie").delete().eq("id", to_del['id']).execute()
                st.rerun()
            except:
                st.error("Błąd: Nie można usunąć kategorii, która zawiera produkty!")

# --- PASEK BOCZNY (USUWANIE PRODUKTÓW) ---
st.sidebar.header("Szybkie Usuwanie Produktów")
if prod_raw:
    p_del = st.sidebar.selectbox("Wybierz produkt", options=prod_raw, format_func=lambda x: x['nazwa'])
    if st.sidebar.button("Usuń wybrany produkt"):
        supabase.table("produkty").delete().eq("id", p_del['id']).execute()
        st.rerun()
