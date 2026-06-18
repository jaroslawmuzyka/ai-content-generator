import streamlit as st
from datetime import datetime
import json
from services.campaign_service import get_campaigns
from services.export_service import get_jobs_for_export, get_all_steps_for_jobs, generate_export_xlsx, log_export, get_export_history
from utils.constants import JOB_STATUSES

def render():
    st.title("📤 Eksport")
    st.write("Pobierz wygenerowane treści i raporty do pliku XLSX.")
    
    tab1, tab2 = st.tabs(["📤 Nowy Eksport", "🗄️ Historia Pobierań"])
    
    with tab1:
        st.subheader("Konfiguracja zakresu danych")
        
        # Szybkie pozyskanie słownika kampanii
        all_camps = get_campaigns("all")
        camp_options = {"all": "Wszystkie kampanie"}
        for c in all_camps: camp_options[c["id"]] = c["name"]
            
        c1, c2, c3 = st.columns(3)
        f_camp = c1.selectbox("Wybierz Kampanię", list(camp_options.keys()), format_func=lambda x: camp_options[x], key="exp_f_camp")
        f_status = c2.selectbox("Tylko o statusie", JOB_STATUSES, index=JOB_STATUSES.index("completed") if "completed" in JOB_STATUSES else 0, help="Domyślnie eksportowane są tylko ukończone zlecenia, by nie zaciemniać tabel logami w toku.")
        f_ctype = c3.selectbox("Typ treści", ["all", "ecommerce_category", "ecommerce_product", "blog_post", "landing_page", "ecommerce_category_mm"])
        
        c4, c5 = st.columns(2)
        f_lang = c4.selectbox("Język", ["all", "pl", "en", "de", "cs", "sk"])
        
        col_d1, col_d2 = c5.columns(2)
        d_from = col_d1.date_input("Utworzono (od)", value=None)
        d_to = col_d2.date_input("Utworzono (do)", value=None)
        
        st.divider()
        
        # Szybki podgląd zadań
        preview_jobs = get_jobs_for_export(f_camp, f_status, f_ctype, f_lang, d_from, d_to)
        
        if not preview_jobs:
            st.info("ℹ️ Brak zadań pasujących do obecnych filtrów.")
        else:
            st.markdown(f"### Podgląd ({len(preview_jobs)} znalezionych zadań)")
            import pandas as pd
            df_preview = pd.DataFrame([{
                "ID": j["id"],
                "Fraza Kluczowa": j.get("main_keyword", ""),
                "Typ": j.get("content_type", ""),
                "Język": j.get("language", ""),
                "Status": j.get("status", ""),
                "Utworzono": j.get("created_at", "")[:16].replace('T', ' ')
            } for j in preview_jobs])
            
            st.dataframe(df_preview, use_container_width=True, hide_index=True)
            
            st.write("Kliknij poniżej, aby przygotować ostateczny plik Excel z pełnymi danymi (w tym wygenerowane treści).")

        if st.button("🚀 Uruchom Konstruktora XLSX", type="primary", disabled=not preview_jobs):
            with st.spinner("Szukanie i zliczanie zadań spełniających kryteria..."):
                jobs = preview_jobs
                
            if not jobs:
                st.warning("⚠️ Nie znaleziono ani jednego zadania w bazie danych pasującego do Twoich filtrów. (Zmień status lub kampanię).")
            else:
                with st.spinner(f"Agregowanie wielopoziomowych logów (ilość zadań: {len(jobs)})..."):
                    job_ids = [j["id"] for j in jobs]
                    steps = get_all_steps_for_jobs(job_ids)
                    
                with st.spinner("Przetwarzanie komórek Excela do pamięci RAM..."):
                    xlsx_bytes = generate_export_xlsx(jobs, steps)
                    
                # Zapisanie logu i podsumowanie w UI
                filename = f"AiContent_Export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                filters_dict = {
                    "campaign": camp_options.get(f_camp, "all"),
                    "status": f_status,
                    "content_type": f_ctype,
                    "language": f_lang,
                    "date_from": str(d_from) if d_from else "Wszystkie",
                    "date_to": str(d_to) if d_to else "Wszystkie"
                }
                
                op_name = st.session_state.get("current_operator", "N/A")
                log_export(f_camp, op_name, filename, filters_dict)
                
                st.success("✅ Eksport XLSX został przygotowany.")
                
                # Faktyczny guzik pobierania strumienia danych binarnych prosto do maszyny klienckiej (bez zapisywania w repo)
                st.download_button(
                    label="💾 Zapisz plik Excela na komputerze",
                    data=xlsx_bytes,
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="secondary",
                    use_container_width=True
                )
                
    with tab2:
        st.subheader("Dziennik Eksportów (Rewizja)")
        history = get_export_history()
        
        if not history:
            st.info("System nie zanotował jeszcze żadnego eksportu.")
        else:
            st.write("Tu sprawdzisz kto, kiedy i jakie dane wyeksportował ze środowiska.")
            for h in history:
                with st.expander(f"Data: {h['created_at'][:16]} | Plik: {h['file_name']} (Inicjator: {h['operator_name']})"):
                    st.write("**Parametry brzegowe eksportu:**")
                    st.json(h.get("filters_json", {}))
