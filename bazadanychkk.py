import streamlit as st
from supabase import create_client, Client
import pandas as pd

# 1. Konfiguracja połączenia
# Upewnij się, że w st.secrets masz: SUPABASE_URL i SUPABASE_KEY
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Błąd połączenia z Supabase. Sprawdź plik secrets.toml.")
    st.stop()

st.set_page_config(page_title="Zarządzanie Sklepem 2.0", layout="wide")

# --- FUNKCJE POMOCNICZE ---
def fetch_data():
    """Pobiera dane z Supabase i zwraca listy słowników."""
    try:
        # Pobieramy produkty wraz z nazwą kategorii (tzw. join)
        p = supabase.table("produkty").select("*, kategorie(nazwa)").execute()
        k = supabase.table("kategorie").select("*").execute()
        return p.data, k.data
    except Exception as e:
        st.error(f"Błąd pobierania danych: {e}")
        return [], []

# Pobieramy dane na starcie
prod_raw, kat_raw = fetch_data()

st.title("System Zarządzania Magazynem 🛒")

tab1, tab2, tab3 = st.tabs(["📦 Produkty", "📊 Analiza i Alerty", "📂 Kategorie"])

# --- TAB 1: ZARZĄDZANIE PRODUKTAMI ---
with tab1:
    st.header("Lista i Dodawanie Produktów")
    
    # Formularz dodawania
    with st.expander("➕ Dodaj nowy produkt do bazy"):
        if kat_raw:
            kat_options = {item['nazwa']: item['id'] for item in kat_raw}
            with st.form("add_product_form"):
                col1, col2 = st.columns(2)
                p_nazwa = col1.text_input("Nazwa produktu")
                p_kat = col1.selectbox("Kategoria", options=list(kat_options.keys()))
                p_cena = col2.number_input("Cena jedn. (PLN)", min_value=0.0, step=0.01)
                p_ocena = col2.number_input("Ocena (0-5)", min_value=0.0, max_value=5.0, step=0.1)
                
                col3, col4 = st.columns(2)
                p_stan = col3.number_input("Aktualna liczba sztuk", min_value=0, step=1)
                p_min = col4.number_input("Stan minimalny (alert)", min_value=0, step=1)
                
                if st.form_submit_button("Zapisz produkt"):
                    if p_nazwa:
                        supabase.table("produkty").insert({
                            "nazwa": p_nazwa,
                            "kategoria_id": kat_options[p_kat],
                            "liczba": p_stan,
                            "stan_minimalny": p_min,
                            "cena": p_cena,
                            "ocena": p_ocena
                        }).execute()
                        st.success(f"Dodano produkt: {p_nazwa}")
                        st.rerun()
        else:
            st.warning("Najpierw dodaj przynajmniej jedną kategorię!")

    # Wyświetlanie tabeli produktów
    if prod_raw:
        df_p = pd.DataFrame(prod_raw)
        
        # Bezpieczne mapowanie kategorii (aby uniknąć błędu KeyError)
        if 'kategorie' in df_p.columns:
            df_p['kategoria_nazwa'] = df_p['kategorie'].apply(lambda x: x['nazwa'] if isinstance(x, dict) else "Brak")
        
        # Wybieramy tylko dostępne kolumny do wyświetlenia
        cols_to_show = ['id', 'nazwa', 'kategoria_nazwa', 'liczba', 'stan_minimalny', 'cena', 'ocena']
        existing_cols = [c for c in cols_to_show if c in df_p.columns]
        
        st.subheader("Aktualny stan magazynowy")
        st.dataframe(df_p[existing_cols], use_container_width=True, hide_index=True)
    else:
        st.info("Brak produktów w bazie.")

# --- TAB 2: ANALIZA I ALERTY ---
with tab2:
    st.header("Analityka Magazynowa")
    if prod_raw:
        df_a = pd.DataFrame(prod_raw)
        
        # Obliczenia (używamy .get() aby uniknąć błędów przy braku kolumn)
        cena_col = df_a.get('cena', 0)
        liczba_col = df_a.get('liczba', 0)
        stan_min_col = df_a.get('stan_minimalny', 0)
        
        total_value = (cena_col * liczba_col).sum()
        low_stock_df = df_a[liczba_col <= stan_min_col]

        # Widżety statystyk
        m1, m2 = st.columns(2)
        m1.metric("Łączna wartość magazynu", f"{total_value:,.2f} PLN")
        m2.metric("Produkty wymagające dostawy", len(low_stock_df))

        if not low_stock_df.empty:
            st.error("⚠️ ALERTY STANÓW MINIMALNYCH:")
            st.table(low_stock_df[['nazwa', 'liczba', 'stan_minimalny']])
        else:
            st.success("Wszystkie stany powyżej minimum. ✅")
    else:
        st.info("Dodaj produkty, aby zobaczyć analizę.")

# --- TAB 3: KATEGORIE ---
with tab3:
    st.header("Zarządzanie Kategoriami")
    
    with st.form("add_cat"):
        new_cat = st.text_input("Nowa kategoria")
        new_desc = st.text_area("Opis kategorii")
        if st.form_submit_button("Dodaj kategorię"):
            if new_cat:
                supabase.table("kategorie").insert({"nazwa": new_cat, "opis": new_desc}).execute()
                st.rerun()

    if kat_raw:
        df_k = pd.DataFrame(kat_raw)
        st.table(df_k[['id', 'nazwa', 'opis']])
        
        # Usuwanie kategorii
        kat_del = st.selectbox("Wybierz kategorię do usunięcia", options=kat_raw, format_func=lambda x: x['nazwa'])
        if st.button("Usuń wybraną kategorię", type="primary"):
            try:
                supabase.table("kategorie").delete().eq("id", kat_del['id']).execute()
                st.rerun()
            except:
                st.error("Nie można usunąć kategorii, która ma przypisane produkty!")

# --- PASEK BOCZNY: USUWANIE PRODUKTÓW ---
st.sidebar.header("Panel Szybkiego Usuwania")
if prod_raw:
    p_to_del = st.sidebar.selectbox("Wybierz produkt", options=prod_raw, format_func=lambda x: x['nazwa'], key="del_prod")
    if st.sidebar.button("Usuń produkt permanentnie"):
        supabase.table("produkty").delete().eq("id", p_to_del['id']).execute()
        st.sidebar.warning(f"Usunięto: {p_to_del['nazwa']}")
        st.rerun()
