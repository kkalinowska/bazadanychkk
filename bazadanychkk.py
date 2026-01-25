import streamlit as st
from supabase import create_client, Client
import pandas as pd
import io  # Kluczowe do generowania plików

# 1. Połączenie
@st.cache_resource
def init_connection():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"Błąd połączenia z bazą: {e}")
        return None

supabase = init_connection()

# 2. Funkcja pobierania danych
def get_data(table_name):
    try:
        if table_name == "produkty":
            # Join z kategoriami, aby mieć nazwy zamiast ID
            return supabase.table("produkty").select("*, kategorie(nazwa)").execute()
        return supabase.table(table_name).select("*").execute()
    except Exception as e:
        st.error(f"Błąd pobierania danych ({table_name}): {e}")
        return None

# Pobieranie danych na start
kategorie_res = get_data("kategorie")
kategorie_list = kategorie_res.data if kategorie_res else []

st.title("Zarządzanie Sklepem 🛒")
tab1, tab2, tab3 = st.tabs(["📦 Produkty", "📂 Kategorie", "📊 Statystyki"])

# --- SEKCJA PRODUKTY (tab1) i KATEGORIE (tab2) pozostają podobne jak wcześniej ---
# (Pominąłem dla czytelności, skupiając się na błędzie w statystykach)

with tab2:
    st.header("Kategorie")
    if kategorie_list:
        st.dataframe(pd.DataFrame(kategorie_list), use_container_width=True)

with tab1:
    st.header("Produkty")
    produkty_res = get_data("produkty")
    if produkty_res and produkty_res.data:
        df_p = pd.DataFrame(produkty_res.data)
        st.dataframe(df_p, use_container_width=True)

# --- SEKCJA: STATYSTYKI I EXCEL (Tu najczęściej występuje błąd) ---
with tab3:
    st.header("Stan Magazynowy i Eksport")
    
    prod_res = get_data("produkty")
    if prod_res and prod_res.data:
        df_stat = pd.DataFrame(prod_res.data)
        
        # 1. Czyszczenie danych (naprawa nazw kategorii)
        if 'kategorie' in df_stat.columns:
            df_stat['kategoria'] = df_stat['kategorie'].apply(lambda x: x.get('nazwa') if isinstance(x, dict) else "Brak")
        
        # 2. Wizualizacja stanu
        st.subheader("Wykres ilości towaru")
        st.bar_chart(data=df_stat, x="nazwa", y="liczba")

        # 3. Alerty niskiego stanu
        niskie_stany = df_stat[df_stat['liczba'] < 5]
        if not niskie_stany.empty:
            st.warning(f"⚠️ Uwaga! {len(n
