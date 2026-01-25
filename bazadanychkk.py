import streamlit as st
from supabase import create_client, Client
import pandas as pd

# --- KONFIGURACJA POŁĄCZENIA ---
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

st.set_page_config(page_title="Zarządzanie Sklepem", layout="wide")
st.title("Zarządzanie Sklepem 🛒")

# --- FUNKCJE POMOCNICZE ---
def get_data(table_name):
    return supabase.table(table_name).select("*").execute()

# Pobieramy dane na początku, by były dostępne globalnie
kategorie_res = get_data("kategorie")
produkty_res = get_data("produkty")

df_kat = pd.DataFrame(kategorie_res.data) if kategorie_res.data else pd.DataFrame()
df_prod = pd.DataFrame(produkty_res.data) if produkty_res.data else pd.DataFrame()

# --- ZAKŁADKI ---
tab1, tab2, tab3 = st.tabs(["📦 Produkty", "📂 Kategorie", "📊 Statystyki"])

# --- SEKCJA: KATEGORIE ---
with tab2:
    st.header("Zarządzanie Kategoriami")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        with st.form("add_category"):
            st.subheader("Dodaj kategorię")
            kat_nazwa = st.text_input("Nazwa kategorii")
            kat_opis = st.text_area("Opis")
            submit_kat = st.form_submit_button("Zapisz kategorię")
            
            if submit_kat and kat_nazwa:
                supabase.table("kategorie").insert({"nazwa": kat_nazwa, "opis": kat_opis}).execute()
                st.success("Dodano kategorię!")
                st.rerun()

    with col2:
        if not df_kat.empty:
            st.subheader("Lista kategorii")
            st.dataframe(df_kat[['id', 'nazwa', 'opis']], use_container_width=True)
            
            kat_to_delete = st.selectbox("Usuń kategorię", options=df_kat['id'].tolist(), 
                                         format_func=lambda x: df_kat[df_kat['id']==x]['nazwa'].values[0])
            if st.button("Usuń wybraną kategorię"):
                supabase.table("kategorie").delete().eq("id", kat_to_delete).execute()
                st.rerun()

# --- SEKCJA: PRODUKTY ---
with tab1:
    st.header("Zarządzanie Produktami")

    if not df_kat.empty:
        with st.expander("➕ Dodaj nowy produkt"):
            with st.form("add_product"):
                p_nazwa = st.text_input("Nazwa produktu")
                col_a, col_b, col_c = st.columns(3)
                p_liczba = col_a.number_input("Liczba (szt.)", min_value=0, step=1)
                p_cena = col_b.number_input("Cena (PLN)", min_value=0.0, step=0.01)
                p_ocena = col_c.number_input
