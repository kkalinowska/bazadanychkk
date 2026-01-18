import streamlit as st
from st_supabase_connection import SupabaseConnection

st.set_page_config(page_title="Magazyn Supabase", layout="wide")

# Inicjalizacja połączenia
conn = st.connection("supabase", type=SupabaseConnection)

st.title("📊 Zarządzanie Bazą Danych (Supabase)")

# Pobieranie danych do list wyboru
def get_categories():
    res = conn.table("kategorie").select("id, nazwa").execute()
    return {c['nazwa']: c['id'] for c in res.data}

categories_dict = get_categories()

# --- SEKCJA KATEGORII ---
st.header("📂 Kategorie")
c_col1, c_col2 = st.columns(2)

with c_col1:
    with st.expander("➕ Dodaj nową kategorię"):
        c_nazwa = st.text_input("Nazwa kategorii")
        c_opis = st.text_area("Opis kategorii")
        if st.button("Zapisz kategorię"):
            conn.table("kategorie").insert({"nazwa": c_nazwa, "opis": c_opis}).execute()
            st.success("Dodano kategorię!")
            st.rerun()

with c_col2:
    with st.expander("🗑️ Usuń kategorię"):
        if categories_dict:
            cat_to_del = st.selectbox("Wybierz kategorię", list(categories_dict.keys()), key="del_cat")
            if st.button("Usuń kategorię i jej produkty", type="primary"):
                conn.table("kategorie").delete().eq("id", categories_dict[cat_to_del]).execute()
                st.warning("Usunięto pomyślnie!")
                st.rerun()

st.divider()

# --- SEKCJA PRODUKTÓW ---
st.header("🛒 Produkty")
p_col1, p_col2 = st.columns([1, 2])

with p_col1:
    st.subheader("Dodaj Produkt")
    p_nazwa = st.text_input("Nazwa produktu")
    p_liczba = st.number_input("Liczba (szt.)", min_value=0, step=1)
    p_ocena = st.number_input("Ocena", min_value=0.0, max_value=5.0, step=0.1)
    p_cat_name = st.selectbox("Kategoria", list(categories_dict.keys()))
    
    if st.button("Dodaj Produkt"):
        new_prod = {
            "nazwa": p_nazwa,
            "liczba": p_liczba,
            "ocena": p_ocena,
            "kategoria_id": categories_dict[p_cat_name]
        }
        conn.table("produkty").insert(new_prod).execute()
        st.success("Produkt dodany!")
        st.rerun()

with p_col2:
    st.subheader("Aktualny Inwentarz")
    # Pobieranie produktów z joinem do kategorii
    prods = conn.table("produkty").select("id, nazwa, liczba, ocena, kategorie(nazwa)").execute()
    
    if prods.data:
        for p in prods.data:
            col_a, col_b, col_c = st.columns([3, 1, 1])
            col_a.write(f"**{p['nazwa']}** ({p['kategorie']['nazwa']}) | Ilość: {p['liczba']} | ⭐ {p['ocena']}")
            if col_c.button("Usuń", key=f"p_{p['id']}"):
                conn.table("produkty").delete().eq("id", p['id']).execute()
                st.rerun()
    else:
        st.info("Brak produktów w bazie.")
