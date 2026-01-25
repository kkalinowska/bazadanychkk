tab1, tab2, tab3 = st.tabs(["📦 Produkty", "📂 Kategorie", "📊 Statystyki"])

# --- SEKCJA: STATYSTYKI ---
with tab3:
    st.header("Analityka i Eksport")
    
    # Pobieramy aktualne dane
    prod_data = get_data("produkty").data
    if prod_data:
        df_stat = pd.DataFrame(prod_data)
        
        # Przetwarzanie nazwy kategorii dla czytelności
        if 'kategorie' in df_stat.columns:
            df_stat['kategoria'] = df_stat['kategorie'].apply(lambda x: x.get('nazwa') if isinstance(x, dict) else 'Brak')

        # --- WIZUALIZACJA STANU ---
        st.subheader("Stan magazynowy (TOP 10)")
        # Wykres słupkowy ilości produktów
        st.bar_chart(df_stat.set_index('nazwa')['liczba'])

        # --- GENEROWANIE EXCELA ---
        st.subheader("Eksport danych")
        
        # Przygotowanie bufora dla pliku Excel
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            # Wybieramy tylko istotne kolumny do raportu
            df_to_export = df_stat[['id', 'nazwa', 'liczba', 'ocena', 'kategoria']]
            df_to_export.to_excel(writer, index=False, sheet_name='Stan Magazynowy')
            
        st.download_button(
            label="📥 Pobierz raport Excel",
            data=buffer.getvalue(),
            file_name="raport_magazynowy.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        # --- PODSUMOWANIE METRYK ---
        st.divider()
        m1, m2, m3 = st.columns(3)
        m1.metric("Suma produktów", df_stat['liczba'].sum())
        m2.metric("Liczba pozycji", len(df_stat))
        m3.metric("Średnia ocena", round(df_stat['ocena'].mean(), 2))
    else:
        st.info("Brak danych do wygenerowania statystyk.")
