import streamlit as st
from supabase import create_client, Client
import pandas as pd

# --- KONFIGURACJA ---
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

st.set_page_config(page_title="Zarządzanie Sklepem", layout="wide")
st.title("Zarządzanie Sklepem 🛒")

# --- POBIERANIE DANYCH ---
def get_data(table_name):
    try:
        return supabase.table(table_name).select("*").execute()
    except Exception as e:
        st.error(f"Błąd pobierania z {table_name}: {e}")
        return None

res_kat = get_data("kategorie")
res_prod = get_data("produkty")

df_kat = pd.DataFrame(res_kat.data) if res_kat and res_kat.data else pd.DataFrame()
df_prod = pd.DataFrame(res_prod.data) if res_prod and res_prod.data else pd.DataFrame()

# --- ZAKŁADKI ---
tab1, tab2, tab3 = st.tabs(["📦 Produkty", "📂 Kategorie", "📊 Statystyki"])

# --- TAB 2: KATEGORIE ---
with tab2:
    st.header("Kategorie")
    col_k1, col_k2 = st.columns([1, 2])
    
    with col_k1:
        with st.form("form_kat"):
            nowa_kat = st.text_input("Nazwa nowej kategorii")
            opis_kat = st.text_area("Opis")
            if st.form_submit_button("Dodaj kategorię") and nowa_kat:
                supabase.table("kategorie").insert({"nazwa": nowa_kat, "opis": opis_kat}).execute()
                st.success("Dodano!")
                st.rerun()
    
    with col_k2:
        if not df_kat.empty:
            st.dataframe(df_kat, use_container_width=True)

# --- TAB 1: PRODUKTY ---
with tab1:
    st.header("Produkty")
    
    if not df_kat.empty:
        with st.expander("➕ Dodaj nowy produkt", expanded=True):
            with st.form("form_produkt"):
                p_nazwa = st.text_input("Nazwa produktu")
                c1, c2 = st.columns(2)
                p_liczba = c1.number_input("Liczba (szt.)", min_value=0)
                p_cena = c2.number_input("Cena (PLN)", min_value=0.0)
                
                # Dynamiczne pobieranie kategorii
                kat_dict = dict(zip(df_kat['nazwa'], df_kat['id']))
                p_kat = st.selectbox("Kategoria", options=list(kat_dict.keys()))
                
                # PRZYCISK - musi być wewnątrz bloku form!
                submit = st.form_submit_button("Zapisz produkt w bazie")
                
                if submit and p_nazwa:
                    data_to_insert = {
                        "nazwa": p_nazwa,
                        "liczba": p_liczba,
                        "kategoria_id": kat_dict[p_kat]
                    }
                    # Dodajemy opcjonalne kolumny tylko jeśli istnieją w bazie
                    if 'cena' in df_prod.columns or True: data_to_insert["cena"] = p_cena
                    
                    supabase.table("produkty").insert(data_to_insert).execute()
                    st.rerun()

        st.subheader("Aktualny asortyment")
        if not df_prod.empty:
            #
