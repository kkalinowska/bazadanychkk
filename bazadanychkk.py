import streamlit as st
from supabase import create_client, Client
import pandas as pd
import segno
import io

# ... (Twój dotychczasowy kod połączenia i funkcje pomocnicze) ...

# Dodajmy nową zakładkę
tab1, tab2, tab3 = st.tabs(["Produkty", "Kategorie", "🛒 Składanie Zamówienia"])

# --- SEKCJA: ZAMÓWIENIA ---
with tab3:
    st.header("Nowe Zamówienie")
    
    produkty_data = get_data("produkty")
    if produkty_data.data:
        df_p = pd.DataFrame(produkty_data.data)
        
        with st.form("order_form"):
            # Wybór produktu
            wybrany_produkt = st.selectbox(
                "Wybierz produkt", 
                options=df_p['id'].tolist(),
                format_func=lambda x: df_p[df_p['id']==x]['nazwa'].values[0]
            )
            ilosc = st.number_input("Ilość", min_value=1, step=1)
            submit_order = st.form_submit_button("Złóż zamówienie i generuj QR")

            if submit_order:
                prod_row = df_p[df_p['id'] == wybrany_produkt].iloc[0]
                
                # Sprawdzenie stanu magazynowego
                if prod_row['liczba'] >= ilosc:
                    nowa_liczba = prod_row['liczba'] - ilosc
                    
                    # 1. Aktualizacja stanu w bazie
                    supabase.table("produkty").update({"liczba": nowa_liczba}).eq("id", wybrany_produkt).execute()
                    
                    # 2. Rejestracja zamówienia
                    order_ref = f"ORD-{wybrany_produkt}-{pd.Timestamp.now().strftime('%M%S')}"
                    supabase.table("zamowienia").insert({
                        "produkt_id": wybrany_produkt,
                        "ilosc": ilosc,
                        "kod_zamowienia": order_ref
                    }).execute()
                    
                    st.success(f"Zamówienie {order_ref} złożone!")

                    # 3. Generowanie kodu QR
                    qr = segno.make(f"Zamowienie: {order_ref}\nProdukt: {prod_row['nazwa']}\nIlosc: {ilosc}")
                    
                    # Zapis do bufora, aby Streamlit mógł to wyświetlić
                    out = io.BytesIO()
                    qr.save(out, kind='png', scale=10)
                    st.image(out.getvalue(), caption=f"Kod QR dla zamówienia {order_ref}")
                    
                    # Opcjonalnie: Przycisk pobierania
                    st.download_button("Pobierz kod QR", data=out.getvalue(), file_name=f"{order_ref}.png", mime="image/png")
                else:
                    st.error(f"Brak wystarczającej ilości towaru! Dostępne: {prod_row['liczba']}")
    else:
        st.info("Brak produktów w bazie.")
