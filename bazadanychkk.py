import streamlit as st
from supabase import create_client, Client
import pandas as pd
import plotly.express as px

# --- 1. KONFIGURACJA ---
st.set_page_config(page_title="Magazyn Pro", layout="wide")

@st.cache_resource
def init_connection():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error("Blad konfiguracji secrets.toml")
        st.stop()

supabase = init_connection()

# --- 2. DANE ---
@st.cache_data(ttl=600)
def fetch_data():
    try:
        p_res = supabase.table("produkty").select("*, kategorie(nazwa)").execute()
        k_res = supabase.table("kategorie").select("*").execute()
        return p_res.data, k_res.data
    except Exception as e:
        return [], []

def refresh():
    st.cache_data.clear()
    st.rerun()

prod_raw, kat_raw = fetch_data()
df_p = pd.DataFrame(prod_raw)
df_k = pd.DataFrame(kat_raw)

# --- 3. ANALIZA ---
total_val = 0
if not df_p.empty:
    if "kategorie" in df_p.columns:
        df_p["kategoria_nazwa"] = df_p["kategorie"].apply(lambda x: x["nazwa"] if isinstance(x, dict) else "Brak")
    df_p["wartosc_suma"] = df_p["cena"] * df_p["liczba"]
    total_val = df_p["wartosc_suma"].sum()

# --- 4. UI ---
st.title("System Magazynowy")

tab1, tab2, tab3 = st.tabs(["Magazyn", "Raporty", "Kategorie"])

with tab1:
    col_a, col_b = st.columns([1, 3])
    with col_a:
        st.metric("Suma wartosci", f"{total_val:,.2f} PLN")
        if not df_p.empty:
            low_stock = df_p[df_p["liczba"] <= df_p["stan_minimalny"]]
            if not low_stock.empty:
                st.warning("Niskie stany!")
                for _, r in low_stock.iterrows():
                    st.write(f"- {r['nazwa']}")

    with col_b:
        if not df_p.empty:
            edited = st.data_editor(
                df_p[["id", "nazwa", "kategoria_nazwa", "cena", "liczba", "stan_minimalny"]],
                use_container_width=True, hide_index=True,
                disabled=["id", "kategoria_nazwa"]
            )
            if st.button("Zapisz zmiany w tabeli"):
                for _, row in edited.iterrows():
                    supabase.table("produkty").update({
                        "cena": row["cena"], "liczba": row["liczba"], "stan_minimalny": row["stan_minimalny"]
                    }).eq("id", row["id"]).execute()
                refresh()

        with st.expander("Dodaj produkt"):
            if not df_k.empty:
                k_map = {r["nazwa"]: r["id"] for r in kat_raw}
                with st.form("form_dodaj_prod"):
                    nazwa = st.text_input("Nazwa")
                    kat = st.selectbox("Kategoria", options=list(k_map.keys()))
                    c1, c2 = st.columns(2)
                    cena = c1.number_input("Cena", min_value=0.0)
                    ilosc = c2.number_input("Ilosc", min_value=0)
                    if st.form_submit_button("Dodaj"):
                        if nazwa:
                            supabase.table("produkty").insert({
                                "nazwa": nazwa, "kategoria_id": k_map[kat],
                                "cena": cena, "liczba": ilosc, "stan_minimalny": 5
                            }).execute()
                            refresh()

with tab2:
    if not df_p.empty:
        fig = px.pie(df_p, values="wartosc_suma", names="kategoria_nazwa", title="Wartosc wg kategorii")
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    with st.form("form_dodaj_kat"):
        nowa_kat = st.text_input("Nowa kategoria")
        if st.form_submit_button("Dodaj kategorie"):
            if nowa_kat:
                supabase.table("kategorie").insert({"nazwa": nowa_kat}).execute()
                refresh()
    if not df_k.empty:
        st.table(df_k[["nazwa"]])

st.sidebar.title("Opcje")
if not df_p.empty:
    p_del = st.sidebar.selectbox("Usun produkt", options=prod_raw, format_func=lambda x: x["nazwa"])
    if st.sidebar.button("Potwierdz usuniecie"):
        supabase.table("produkty").delete().eq("id", p_del["id"]).execute()
        refresh()
