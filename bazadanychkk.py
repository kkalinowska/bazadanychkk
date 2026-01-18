import streamlit as st
from supabase import create_client, Client
import pandas as pd

# Konfiguracja połączenia z Supabase
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.title("Zarządzanie Sklepem 🛒")

# Funkcje pomocnicze
def get_data(table_name):
    return supabase.table(table_name).select("*").execute()

# --- ZAKŁADKI ---
tab1, tab2 = st.tabs(["Produkty", "Kategorie"])

# --- SEKCJA: KATEGORIE ---
with tab2:
    st.header("Zarządzanie Kategoriami")
    
    # Dodawanie kategorii
    with st.expander("Dodaj nową kategorię"):
        with st.form("add_category"):
            kat_nazwa = st.text_input("Nazwa kategorii")
            kat_opis = st.text_area("Opis")
            submit_kat = st.form_submit_button("Zapisz kategorię")
            
            if submit_kat and kat_nazwa:
                supabase.table("kategorie").insert({"nazwa": kat_nazwa, "opis": kat_opis}).execute()
                st.success("Dodano kategorię!")
                st.rerun()

    # Wyświetlanie i usuwanie kategorii
    kategorie_data = get_data("kategorie")
    if kategorie_data.data:
        df_kat = pd.DataFrame(kategorie_data.data)
        st.table(df_kat)
        
        kat_to_delete = st.selectbox("Wybierz kategorię do usunięcia", options=df_kat['id'].tolist(), format_func=lambda x: df_kat[df_kat['id']==x]['nazwa'].values[0])
        if st.button("Usuń kategorię"):
            supabase.table("kategorie").delete().eq("id", kat_to_delete).execute()
            st.warning(f"Usunięto kategorię ID: {kat_to_delete}")
            st.rerun()

# --- SEKCJA: PRODUKTY ---
with tab1:
    st.header("Zarządzanie Produktami")

    # Dodawanie produktu
    if kategorie_data.data:
        kat_options = {item['nazwa']: item['id'] for item in kategorie_data.data}
        
        with st.expander("Dodaj nowy produkt"):
            with st.form("add_product"):
                p_nazwa = st.text_input("Nazwa produktu")
                p_liczba = st.number_input("Liczba (szt.)", min_value=0, step=1)
                p_ocena = st.number_input("Ocena", min_value=0.0, max_value=5.0, step=0.1)
                p_kat_nazwa = st.selectbox("Kategoria", options=list(kat_options.keys()))
                submit_p = st.form_submit_button("Zapisz produkt")
                
                if submit_p and p_nazwa:
                    supabase.table("produkty").insert({
                        "nazwa": p_nazwa,
                        "liczba": p_liczba,
                        "ocena": p_ocena,
                        "kategoria_id": kat_options[p_kat_nazwa]
                    }).execute()
                    st.success("Dodano produkt!")
                    st.rerun()
    else:
        st.warning("Najpierw dodaj kategorię, aby móc przypisać do niej produkty.")

    # Wyświetlanie i usuwanie produktów
    produkty_data = get_data("produkty")
    if produkty_data.data:
        df_prod = pd.DataFrame(produkty_data.data)
        st.dataframe(df_prod)
        
        prod_to_delete = st.selectbox("Wybierz produkt do usunięcia", options=df_prod['id'].tolist(), format_func=lambda x: df_prod[df_prod['id']==x]['nazwa'].values[0])
        if st.button("Usuń produkt"):
            supabase.table("produkty").delete().eq("id", prod_to_delete).execute()
            st.warning(f"Usunięto produkt ID: {prod_to_delete}")
            st.rerun()
