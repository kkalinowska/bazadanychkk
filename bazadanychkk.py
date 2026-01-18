import streamlit as st
import sqlite3
import pandas as pd

# Konfiguracja bazy danych
def init_db():
    conn = sqlite3.connect('sklep.db', check_same_thread=False)
    c = conn.cursor()
    # Tabela Kategorie
    c.execute('''CREATE TABLE IF NOT EXISTS kategorie (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nazwa TEXT NOT NULL,
                    opis TEXT)''')
    # Tabela Produkty z kluczem obcym
    c.execute('''CREATE TABLE IF NOT EXISTS produkty (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nazwa TEXT NOT NULL,
                    liczba INTEGER,
                    ocena REAL,
                    kategoria_id INTEGER,
                    FOREIGN KEY (kategoria_id) REFERENCES kategorie(id) ON DELETE CASCADE)''')
    conn.commit()
    return conn

conn = init_db()
c = conn.cursor()

st.title("📦 System Zarządzania Produktami")

menu = ["Produkty", "Kategorie"]
choice = st.sidebar.selectbox("Menu", menu)

# --- SEKCJA KATEGORIE ---
if choice == "Kategorie":
    st.header("Zarządzanie Kategoriami")
    
    with st.expander("Dodaj nową kategorię"):
        nazwa_kat = st.text_input("Nazwa kategorii")
        opis_kat = st.text_area("Opis")
        if st.button("Dodaj kategorię"):
            c.execute("INSERT INTO kategorie (nazwa, opis) VALUES (?, ?)", (nazwa_kat, opis_kat))
            conn.commit()
            st.success(f"Dodano kategorię: {nazwa_kat}")

    st.subheader("Lista kategorii")
    kat_df = pd.read_sql_query("SELECT * FROM kategorie", conn)
    st.dataframe(kat_df, use_container_width=True)

    with st.expander("Usuń kategorię"):
        kat_to_del = st.selectbox("Wybierz kategorię do usunięcia", kat_df['nazwa'].tolist() if not kat_df.empty else [])
        if st.button("Usuń"):
            c.execute("DELETE FROM kategorie WHERE nazwa = ?", (kat_to_del,))
            conn.commit()
            st.warning(f"Usunięto kategorię i powiązane produkty!")
            st.rerun()

# --- SEKCJA PRODUKTY ---
else:
    st.header("Zarządzanie Produktami")
    
    with st.expander("Dodaj nowy produkt"):
        nazwa_prod = st.text_input("Nazwa produktu")
        liczba = st.number_input("Liczba", min_value=0, step=1)
        ocena = st.number_input("Ocena", min_value=0.0, max_value=5.0, step=0.1)
        
        # Pobieranie kategorii do selectboxa
        kat_data = pd.read_sql_query("SELECT id, nazwa FROM kategorie", conn)
        kat_dict = dict(zip(kat_data['nazwa'], kat_data['id']))
        wybrana_kat = st.selectbox("Kategoria", list(kat_dict.keys()))

        if st.button("Dodaj produkt"):
            c.execute("""INSERT INTO produkty (nazwa, liczba, ocena, kategoria_id) 
                         VALUES (?, ?, ?, ?)""", (nazwa_prod, liczba, ocena, kat_dict[wybrana_kat]))
            conn.commit()
            st.success(f"Dodano produkt: {nazwa_prod}")

    st.subheader("Aktualny stan magazynowy")
    query = """
    SELECT p.id, p.nazwa, p.liczba, p.ocena, k.nazwa as kategoria 
    FROM produkty p 
    LEFT JOIN kategorie k ON p.kategoria_id = k.id
    """
    prod_df = pd.read_sql_query(query, conn)
    st.dataframe(prod_df, use_container_width=True)

    with st.expander("Usuń produkt"):
        prod_id = st.number_input("Podaj ID produktu do usunięcia", min_value=1, step=1)
        if st.button("Usuń produkt"):
            c.execute("DELETE FROM produkty WHERE id = ?", (prod_id,))
            conn.commit()
            st.info(f"Usunięto produkt o ID: {prod_id}")
            st.rerun()
