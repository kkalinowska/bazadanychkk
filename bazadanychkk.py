import streamlit as st
from st_supabase_connection import SupabaseConnection

st.set_page_config(page_title="Zarządzanie Asortymentem", layout="wide")

# Inicjalizacja połączenia
conn = st.connection("supabase", type=SupabaseConnection)

st.title("📦 System Zarządzania Produktami")

# --- SEKCJA KATEGORII ---
st.header("📂 Kategorie")
col1, col2 = st.columns(2)

with col1:
    st.subheader("Dodaj Kategorię")
    new_cat = st.text_input("Nazwa nowej kategorii")
    if st.button("Dodaj Kategorię"):
        if new_cat:
            conn.table("categories").insert({"name": new_cat}).execute()
            st.success(f"Dodano kategorię: {new_cat}")
            st.rerun()

with col2:
    st.subheader("Usuń Kategorię")
    cats = conn.table("categories").select("id, name").execute()
    cat_options = {c['name']: c['id'] for c in cats.data}
    
    cat_to_delete = st.selectbox("Wybierz kategorię do usunięcia", options=list(cat_options.keys()))
    if st.button("Usuń Kategorię", type="primary"):
        conn.table("categories").delete().eq("id", cat_options[cat_to_delete]).execute()
        st.warning(f"Usunięto kategorię i powiązane produkty")
        st.rerun()

st.divider()

# --- SEKCJA PRODUKTÓW ---
st.header("🛒 Produkty")
p_col1, p_col2 = st.columns(2)

with p_col1:
    st.subheader("Dodaj Produkt")
    p_name = st.text_input("Nazwa produktu")
    p_price = st.number_input("Cena", min_value=0.0, step=0.01)
    p_cat = st.selectbox("Kategoria produktu", options=list(cat_options.keys()))
    
    if st.button("Dodaj Produkt"):
        payload = {
            "name": p_name,
            "price": p_price,
            "category_id": cat_options[p_cat]
        }
        conn.table("products").insert(payload).execute()
        st.success("Produkt dodany!")
        st.rerun()

with p_col2:
    st.subheader("Lista i Usuwanie Produktów")
    products = conn.table("products").select("id, name, price, categories(name)").execute()
    
    for p in products.data:
        col_p1, col_p2 = st.columns([3, 1])
        col_p1.write(f"**{p['name']}** - {p['price']} PLN ({p['categories']['name']})")
        if col_p2.button("Usuń", key=f"del_{p['id']}"):
            conn.table("products").delete().eq("id", p['id']).execute()
            st.rerun()
