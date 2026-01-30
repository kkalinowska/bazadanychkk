import streamlit as st
from supabase import create_client, Client
import pandas as pd
import plotly.express as px

# --- 1. KONFIGURACJA STRONY ---
st.set_page_config(page_title="Magazyn Pro", layout="wide")

# --- 2. POLACZENIE Z SUPABASE ---
@st.cache_resource
def init_connection():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error("Blad polaczenia. Sprawdz plik secrets.toml")
        st.stop()

supabase = init_connection()

# --- 3. POBIERANIE DANYCH ---
@st.cache_data(ttl=600)
def fetch_data():
    try:
        p_res = supabase.table("produkty").select("*, kategorie(nazwa)").execute()
        k_res = supabase.table("kategorie").select("*").execute()
        return p_res.data, k_res.data
    except Exception as e:
        st.error(f"Blad bazy danych: {e}")
        return [], []

def refresh():
    st.cache_data.clear()
    st.rerun()

prod_raw, kat_raw = fetch_data()
df_p = pd.DataFrame(prod_raw)
df_k = pd.DataFrame(kat_raw)

# --- 4. LOGIKA ANALITYCZNA ---
total_val = 0
low_stock_count = 0

if not df_p.empty:
    if 'kategorie' in df_p.columns:
        df_p['kategoria_nazwa'] = df_p['kategorie'].apply(lambda x: x['nazwa'] if isinstance(x, dict) else "Brak")
    
    df_p['wartosc_laczna'] = df_p['cena'] * df_p['liczba']
    total_val = df_p['wartosc_laczna'].sum()
    low_stock_df = df_p[df_p['liczba'] <= df_p['stan_minimalny']]
    low_stock_count = len(low_stock_df)

# --- 5. INTERFEJS UZYTKOWNIKA ---
st.title("Zarzadzanie Magazynem")

t1, t2, t3 = st.tabs(["Magazyn", "Raporty", "Kategorie"])

# --- TAB 1: MAGAZYN ---
with t1:
    col_a, col_b = st.columns([1, 3])
    
    with col_a:
        st.subheader("Status")
        st.metric("Wartosc towaru", f"{total_val:,.2f} PLN")
        st.metric("Niskie stany", low_stock_count)
        
        if low_stock_count > 0:
            st.warning("Braki:")
            for _, r in low_stock_df.iterrows():
                st.caption(f"- {r['nazwa']} (szt: {r['liczba']})")

    with col_b:
        st.subheader("Lista produktow")
        if not df_p.empty:
            edited = st.data_editor(
                df_p[['id', 'nazwa', 'kategoria_nazwa', 'cena', 'liczba', 'stan_minimalny']],
                use_container_width=True,
                hide_index=True,
                disabled=['id', 'kategoria_nazwa']
            )
            
            if st.button("Zapisz zmiany w tabeli"):
                for idx, row in edited.iterrows():
                    supabase.table("produkty").update({
                        "cena": row["cena"],
                        "liczba": row["liczba"],
                        "stan_minimalny": row["stan_minimalny"]
                    }).eq("id", row["id"]).execute()
                st.success("Zaktualizowano dane!")
                refresh()
        
        with st.expander("Dodaj produkt"):
            if not df_k.empty:
                k_map = {row['nazwa']: row['id'] for _, row in df_k.iterrows()}
                with st.form("form_add_prod"):
                    n = st.text_input("Nazwa")
                    kat = st.selectbox("Kategoria", options=list(k_map.keys()))
                    c1, c2 = st.columns(2)
                    pr = c1.number_input("Cena", min_value=0.0)
                    qt = c2.number_input("Ilosc", min_value=0)
                    if st.form_submit_button("Zapisz produkt"):
                        if n:
                            supabase.table("produkty").insert({
                                "nazwa": n, "kategoria_id": k_map[kat],
                                "cena": pr, "liczba": qt, "stan_minimalny": 5
                            }).execute()
                            refresh()
            else:
                st.info("Brak kategorii w bazie.")

# --- TAB 2: RAPORTY ---
with t2:
    if not df_p.empty:
        st.subheader("Analiza")
        fig = px.pie(df_p, values='wartosc_laczna', names='kategoria_nazwa', title="Wartosc wg kategorii")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.write("Brak danych.")

# --- TAB 3: KATEGORIE ---
with t3:
    st.subheader("Kategorie")
    with st.form("form_add_cat"):
        new_c = st.text_input("Nowa kategoria")
        if st.form_submit_button("Dodaj"):
            if new_c:
                supabase.table("kategorie").insert({"nazwa": new_c}).execute()
                refresh()
    
    if not df_k.empty:
        st.dataframe(df_k[['nazwa']], use_container_width=True)

# --- SIDEBAR (USUWANIE) ---
st.sidebar.title("Opcje")
if not df_p.empty:
    p_del = st.sidebar.selectbox("Usun produkt", options=prod_raw, format_func=lambda x: x['nazwa'])
    if st.sidebar.button("Potwierdz usuniecie"):
        supabase.table("produkty").delete().eq("id", p_del['id']).execute()
        refresh()
