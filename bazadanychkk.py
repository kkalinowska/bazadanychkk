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

# Pobieramy dane
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
        with st.form("add_category_form"): # Unikalna nazwa formularza
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
        with st.expander("➕ Dodaj nowy produkt", expanded=True):
            # POPRAWIONY FORMULARZ Z PRZYCISKIEM SUBMIT
            with st.form("add_product_form"):
                p_nazwa = st.text_input("Nazwa produktu")
                
                col_a, col_b = st.columns(2)
                p_liczba = col_a.number_input("Liczba (szt.)", min_value=0, step=1)
                p_cena = col_b.number_input("Cena (PLN)", min_value=0.0, step=0.01)
                
                col_c, col_d = st.columns(2)
                p_ocena = col_c.number_input("Ocena (0-5)", min_value=0.0, max_value=5.0, step=0.1)
                
                kat_options = {item['nazwa']: item['id'] for item in kategorie_res.data}
                p_kat_nazwa = col_d.selectbox("Kategoria", options=list(kat_options.keys()))
                
                # TO JEST KLUCZOWY PRZYCISK, KTÓREGO BRAKOWAŁO:
                submit_p = st.form_submit_button("Zapisz produkt")
                
                if submit_p:
                    if p_nazwa:
                        supabase.table("produkty").insert({
                            "nazwa": p_nazwa,
                            "liczba": p_liczba,
                            "cena": p_cena,
                            "ocena": p_ocena,
                            "kategoria_id": kat_options[p_kat_nazwa]
                        }).execute()
                        st.success("Produkt dodany!")
                        st.rerun()
                    else:
                        st.error("Podaj nazwę produktu!")

        if not df_prod.empty:
            st.subheader("Aktualny asortyment")
            df_display = df_prod.copy()
            kat_map = dict(zip(df_kat['id'], df_kat['nazwa']))
            df_display['kategoria'] = df_display['kategoria_id'].map(kat_map)
            
            st.dataframe(df_display[['id', 'nazwa', 'liczba', 'cena', 'ocena', 'kategoria']], use_container_width=True)
            
            with st.expander("🗑️ Usuwanie produktów"):
                prod_to_delete = st.selectbox("Wybierz produkt do usunięcia", options=df_prod['id'].tolist(), 
                                              format_func=lambda x: df_prod[df_prod['id']==x]['nazwa'].values[0])
                if st.button("Usuń produkt"):
                    supabase.table("produkty").delete().eq("id", prod_to_delete).execute()
                    st.rerun()
    else:
        st.warning("Najpierw dodaj przynajmniej jedną kategorię w zakładce 'Kategorie'.")

# --- SEKCJA: STATYSTYKI ---
with tab3:
    st.header("Analiza Magazynu")
    
    if not df_prod.empty and not df_kat.empty:
        # Obliczenia - upewniamy się, że kolumny są liczbowe
        df_prod['cena'] = pd.to_numeric(df_prod['cena'], errors='coerce').fillna(0)
        df_prod['liczba'] = pd.to_numeric(df_prod['liczba'], errors='coerce').fillna(0)
        df_prod['wartosc_laczna'] = df_prod['liczba'] * df_prod['cena']
        
        # Statystyki ogólne
        c1, c2, c3 = st.columns(3)
        c1.metric("Wszystkich sztuk", int(df_prod['liczba'].sum()))
        c2.metric("Wartość magazynu", f"{df_prod['wartosc_laczna'].sum():,.2f} PLN")
        c3.metric("Liczba pozycji", len(df_prod))
        
        st.divider()
        
        # Grupowanie po kategorii
        stats = df_prod.groupby('kategoria_id').agg({
            'id': 'count',
            'liczba': 'sum',
            'wartosc_laczna': 'sum'
        }).reset_index()
        
        stats = stats.merge(df_kat[['id', 'nazwa']], left_on='kategoria_id', right_on='id')
        stats_display = stats.rename(columns={
            'nazwa': 'Kategoria',
            'id_x': 'Rodzajów towaru',
            'liczba': 'Sztuk łącznie',
            'wartosc_laczna': 'Wartość (PLN)'
        })
        
        st.subheader("Podsumowanie kategorii")
        st.dataframe(stats_display[['Kategoria', 'Rodzajów towaru', 'Sztuk łącznie', 'Wartość (PLN)']], use_container_width=True)
        st.bar_chart(data=stats_display, x='Kategoria', y='Wartość (PLN)')
    else:
        st.info("Brak produktów do wyświetlenia statystyk.")
