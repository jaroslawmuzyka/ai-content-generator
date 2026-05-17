import streamlit as st
import pandas as pd
from services.campaign_service import get_campaigns
from services.job_service import get_campaign_prompt_sets
from services.import_service import generate_template_bytes, validate_uploaded_file, process_import

def render():
    st.title("Masowy Import Zadań (XLSX)")
    st.write("Wgraj listę tysięcy słów kluczowych i adresów URL z pliku Excel, aby zautomatyzować generowanie ogromnych sekcji witryny naraz.")
    
    # ------------------------------------------------------------------
    # KONFIGURACJA POCZĄTKOWA
    # ------------------------------------------------------------------
    all_camps = get_campaigns("active")
    if not all_camps:
        st.warning("⚠️ Zanim zaimportujesz plik, musisz utworzyć w systemie jakąkolwiek aktywną Kampanię.")
        return
        
    camp_options = {c["id"]: c["name"] for c in all_camps}
    
    c1, c2, c3 = st.columns(3)
    
    selected_camp_id = c1.selectbox("1. Wybierz kampanię docelową", list(camp_options.keys()), format_func=lambda x: camp_options[x])
    
    prompt_sets = get_campaign_prompt_sets(selected_camp_id)
    if not prompt_sets:
        st.warning("⚠️ Wybrana kampania nie ma skonfigurowanych żadnych promptów (szablonów). Wejdź w zakładkę 'Prompty' i skopiuj bibliotekę bazową.")
        return
        
    set_options = {s["id"]: s["name"] for s in prompt_sets}
    selected_set_id = c2.selectbox("2. Wybierz szablon promptów (Pipeline)", list(set_options.keys()), format_func=lambda x: set_options[x])
    
    target_status = c3.selectbox("3. Nadaj status po imporcie", ["queued", "draft"], help="'Queued' sprawi, że zadania będą gotowe do odpalenia w kolejce. 'Draft' wymusi na Tobie ich ręczne zatwierdzenie później.")
    
    st.divider()
    
    # ------------------------------------------------------------------
    # POBIERANIE SZABLONU
    # ------------------------------------------------------------------
    st.subheader("Krok 1: Przygotowanie pliku")
    st.write("Skrypt jest rygorystyczny i nie wybacza literówek w nagłówkach kolumn. Pobierz poniższy, pusty szablon, wypełnij go swoimi danymi (zachowując format pierwszej linijki) i wgraj z powrotem.")
    
    st.download_button(
        label="📥 Pobierz oficjalny szablon (.xlsx)",
        data=generate_template_bytes(),
        file_name="Import_Szablon_AI_Content.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary"
    )
    
    st.divider()
    
    # ------------------------------------------------------------------
    # UPLOAD I WALIDACJA W LOCIE
    # ------------------------------------------------------------------
    st.subheader("Krok 2: Wgraj wypełniony plik")
    uploaded_file = st.file_uploader("Przeciągnij plik tutaj...", type=["xlsx"])
    
    if uploaded_file:
        with st.spinner("Skanowanie i walidacja danych (Może potrwać kilka sekund przy dużych plikach)..."):
            valid_records, errors_list = validate_uploaded_file(uploaded_file)
            
        st.markdown(f"**Analiza Zakończona.** Przeskanowano łącznie **{len(valid_records) + len(errors_list)}** rekordów (wierszy).")
        
        tab_ok, tab_err = st.tabs([f"✅ Zwalidowane rekordy ({len(valid_records)})", f"❌ Zawierające błędy ({len(errors_list)})"])
        
        with tab_err:
            if errors_list:
                st.error("Poniższe wiersze nie przeszły rygorystycznej kontroli i zostały ZABLOKOWANE przed importem.")
                st.dataframe(pd.DataFrame(errors_list), use_container_width=True)
            else:
                st.success("Wspaniale! Nie znaleziono żadnych pustych komórek ani błędów strukturalnych.")
                
        with tab_ok:
            if valid_records:
                st.success(f"Te rekordy są czyste i gotowe do wstrzyknięcia do bazy jako nowe, wyizolowane zadania.")
                with st.expander("Podgląd struktury przed dodaniem"):
                    st.dataframe(pd.DataFrame(valid_records).head(50), use_container_width=True)
                
                # Zabezpieczenie przed powtórnym submitem przy rerunach
                if "import_in_progress" not in st.session_state:
                    st.session_state["import_in_progress"] = False
                    
                if st.button("🚀 Wyślij poprawne rekordy do Kolejki", type="primary", use_container_width=True):
                    
                    prog_bar = st.progress(0)
                    prog_txt = st.empty()
                    
                    def on_progress(current, total):
                        pct = min(100, int((current/total)*100))
                        prog_bar.progress(pct)
                        prog_txt.info(f"Klonowanie szablonów AI i przypisywanie do zadania: {current} z {total}...")
                        
                    op_name = st.session_state.get("current_operator", "System Import")
                    
                    with st.spinner("Inicjalizacja transakcji z bazą danych..."):
                        ok, msg = process_import(valid_records, selected_camp_id, selected_set_id, target_status, op_name, on_progress)
                        
                    if ok:
                        prog_bar.progress(100)
                        prog_txt.success(msg)
                        st.balloons()
                    else:
                        prog_txt.error(f"Krytyczna awaria podczas komunikacji z Supabase: {msg}")
            else:
                st.info("Plik nie zawierał ani jednego poprawnego rekordu, lub był pusty. Sprawdź zakładkę z Błędami.")
