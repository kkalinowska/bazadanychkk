import streamlit as st
from supabase import create_client, Client
import pandas as pd

# 1. Konfiguracja połączenia
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Magazyn 2.0", layout="wide")

# --- FUNKCJE DANYCH ---
def fetch_data():
    # Pobieramy produkty z dołączoną nazwą kategorii
    p = supabase.table("produkty").select("*, kategorie(nazwa)").execute()
    k = supabase.table("kategorie").select("*").execute()
    return p.data, k.data

prod_data, kat_data = fetch_data()

# --- INTERFEJS ---
st.title("Zarządzanie Sklepem i Magazynem 🛒")

tab1, tab2, tab3 = st.tabs(["📦 Produkty", "📊 Analiza Magazynu", "📂 Kategorie"])

# --- TAB 1: PRODUKTY ---
with tab1:
    st.header("Lista Produktów")
    
    if prod_data:
        # Przygotowanie DataFrame do wyświetlenia
        df = pd.DataFrame(prod_data)
        
        # Wyliczanie wartości magazynowej (jeśli masz kolumnę 'cena')
        # Zakładam dodanie kolumny 'cena' do tabeli
        if 'cena' in df.columns:
            df['wartosc_brutto'] = df['liczba'] * df['cena']
        
        # Mapowanie nazwy kategorii dla czytelności
        df['kategoria'] = df['kategorie'].apply(lambda x: x['nazwa'] if isinstance(x, dict) else "Brak")
        
        # Wyświetlanie z formatowaniem
        st.dataframe(
            df[['id', 'nazwa', 'kategoria', 'liczba', 'stan_minimalny', 'cena', 'ocena']],
            use_container_width=True,
            hide_index=True
        )
    
    # Formularz dodawania
    with st.expander("➕ Dodaj nowy produkt"):
        if kat_data:
            kat_dict = {k['nazwa']: k['id'] for k in kat_data}
            with st.form("new_product"):
                col1, col2 = st.columns(2)
                nazwa = col1.text_input("Nazwa produktu")
                kat_name = col1.selectbox("Kategoria", options=list(kat_dict.keys()))
                cena = col2.number_input("Cena jedn. (PLN)", min_value=0.0, step=0.01)
                
                col3, col4 = st.columns(2)
                stan = col3.number_input("Aktualny stan", min_value=0)
                stan_min = col4.number_input("Stan minimalny (Alert)", min_value=0)
                
                if st.form_submit_button("Dodaj do bazy"):
                    if nazwa:
                        supabase.table("produkty").insert({
                            "nazwa": nazwa,
                            "kategoria_id": kat_dict[kat_name],
                            "liczba": stan,
                            "stan_minimalny": stan_min,
                            "cena": cena
                        }).execute()
                        st.success("Produkt dodany!")
                        st.rerun()
        else:
            st.warning("Najpierw dodaj kategorię!")

# --- TAB 2: ANALIZA (WARTOŚĆ I ALERTY) ---
with tab3:
    st.header("Kategorie")
    # Tutaj zachowaj swoją logikę dodawania/usuwania kategorii z poprzedniego kodu
    # ... (kod identyczny jak w poprzedniej wersji)

with tab2:
    st.header("Analityka Magazynowa")
    
    if prod_data:
        df_analiza = pd.DataFrame(prod_data)
        
        # 1. Wartość Magazynu
        total_value = (df_analiza['liczba'] * df_analiza.get('cena', 0)).sum()
        
        # 2. Produkty poniżej stanu minimalnego
        # Sprawdzamy gdzie liczba < stan_minimalny
        low_stock = df_analiza[df_analiza['liczba'] <= df_analiza['stan_minimalny']]
        
        col_m1, col_m2 = st.columns(2)
        col_m1.metric("Całkowita wartość towaru", f"{total_value:,.2f} PLN")
        col_m2.metric("Produkty do domówienia", len(low_stock))
        
        if not low_stock.empty:
            st.error("⚠️ UWAGA: Poniższe produkty wymagają uzupełnienia:")
            st.table(low_stock[['nazwa', 'liczba', 'stan_minimalny']])
        else:
            st.success("Wszystkie stany magazynowe w normie! ✅")

# --- USUWANIE ---
st.sidebar.header("Panel usuwania")
if prod_data:
    p_to_del = st.sidebar.selectbox("Usuń produkt", options=prod_data, format_func=lambda x: x['nazwa'])
    if st.sidebar.button("Potwierdź usunięcie"):
        supabase.table("produkty").delete().eq("id", p_to_del['id']).execute()
        st.rerun()
