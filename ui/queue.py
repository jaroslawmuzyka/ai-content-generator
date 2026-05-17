import streamlit as st
from services.job_repository import get_content_jobs, update_job_status, requeue_failed_jobs
from services.job_processor import process_single_job, process_job_batch
from utils.constants import JOB_STATUSES
from services.campaign_service import get_campaigns

def render():
    st.title("Kolejka Zadań")
    st.write("Podgląd i ręczne zarządzanie przepustowością zadań.")
    
    # -------------------------------------------------------------
    # POBIERANIE DANYCH BAZOWYCH I FILTROWANIE
    # -------------------------------------------------------------
    all_camps = get_campaigns("all")
    camp_options = {"all": "Wszystkie kampanie"}
    for c in all_camps:
        camp_options[c["id"]] = c["name"]
        
    c1, c2, c3, c4 = st.columns(4)
    f_camp = c1.selectbox("Wybierz kampanię", list(camp_options.keys()), format_func=lambda x: camp_options[x])
    f_status = c2.selectbox("Filtruj status", JOB_STATUSES)
    f_ctype = c3.selectbox("Typ treści", ["all", "ecommerce_category", "ecommerce_product", "blog_post", "landing_page"])
    f_lang = c4.selectbox("Język", ["all", "pl", "en", "de", "cs", "sk"])
    
    jobs = get_content_jobs(
        campaign_id=f_camp if f_camp != "all" else None,
        status=f_status if f_status != "all" else None,
        content_type=f_ctype if f_ctype != "all" else None,
        language=f_lang if f_lang != "all" else None
    )
    
    st.divider()
    
    # -------------------------------------------------------------
    # PANEL PRZETWARZANIA PARTII (BATCH PROCESSING)
    # -------------------------------------------------------------
    st.subheader("Przetwarzanie partii (Batch Processing)")
    st.write("Wybierz ile zadań chcesz wygenerować jednorazowo w tej sesji przeglądarki. **Zalecane to 5-10 sztuk.**")
    
    b1, b2, b3, b4 = st.columns([1.5, 2, 1, 1])
    
    limit_opts = {1: "Przetwórz 1 zadanie", 5: "Przetwórz 5 zadań", 10: "Przetwórz 10 zadań", 0: "Przetwórz WSZYSTKIE"}
    selected_limit = b1.selectbox("Wielkość partii", list(limit_opts.keys()), format_func=lambda x: limit_opts[x], label_visibility="collapsed")
    batch_camp = b2.selectbox("Kampania źródłowa", list(camp_options.keys()), format_func=lambda x: camp_options[x], label_visibility="collapsed")
    
    if b3.button("▶️ Uruchom", type="primary", use_container_width=True):
        if selected_limit == 0:
            st.session_state["show_batch_warning"] = True
        else:
            st.session_state["start_batch"] = True
            st.session_state["show_batch_warning"] = False
            
    if b4.button("🔄 Ponów błędne", type="secondary", use_container_width=True):
        count = requeue_failed_jobs(batch_camp if batch_camp != "all" else None)
        st.success(f"Zmieniono status {count} zadań ('failed') z powrotem na 'queued'.")
        # Dajemy sekundę na przeczytanie przed rerunem (st.rerun zje alert)
        st.rerun()

    # Alert o uruchamianiu wszystkich zadań
    if st.session_state.get("show_batch_warning"):
        st.warning("⚠️ **UWAGA:** Przetwarzanie wszystkich oczekujących zadań naraz bez użycia workera w tle z dużym prawdopodobieństwem doprowadzi do zawieszenia karty (Timeout Error 504) po jakimś czasie. Rekomendowane jest robienie tego seriami po 10. Czy na pewno chcesz to zrobić?")
        wc1, wc2 = st.columns([1, 6])
        if wc1.button("Tak, podejmuję ryzyko", type="primary"):
            st.session_state["start_batch"] = True
            st.session_state["show_batch_warning"] = False
            st.rerun()
        if wc2.button("Zmień zdanie i anuluj"):
            st.session_state["show_batch_warning"] = False
            st.rerun()

    # Logika startu batcha (maszyny stanów)
    if st.session_state.get("start_batch"):
        st.session_state["start_batch"] = False # Blokada przed nieskończoną pętlą
        
        limit_val = None if selected_limit == 0 else selected_limit
        c_id_val = batch_camp if batch_camp != "all" else None
        
        st.markdown("---")
        st.write(f"### ⚙️ Generowanie masowe w toku...")
        
        batch_prog = st.progress(0)
        batch_status = st.empty()
        
        job_prog = st.progress(0)
        job_status = st.empty()
        
        # Callbacks
        def on_batch(idx, total, job, successes, errors):
            pct = int((idx / total) * 100) if total > 0 else 100
            batch_prog.progress(pct)
            if job:
                batch_status.markdown(f"**Partia ({idx+1}/{total})** | Wykonywane fraza: `{job['main_keyword']}` | ✅ Sukcesy: `{successes}` | ❌ Błędy: `{errors}`")
            else:
                batch_status.success(f"**Koniec!** Przetworzono {total} zadań w tej partii. (✅ {successes} | ❌ {errors})")
                
        def on_job(step_name, current, total):
            pct = min(100, int((current / total) * 100)) if total > 0 else 100
            job_prog.progress(pct)
            job_status.info(f"Krok bieżącego zadania: **{step_name}** ({current+1}/{total})")
            
        with st.spinner("AI przetwarza zlecenia sekwencyjnie. Nie zamykaj tej karty!"):
            total_ran, ok_cnt, err_cnt = process_job_batch(limit_val, c_id_val, on_batch, on_job)
            
        if total_ran == 0:
            st.info("Obecnie w kolejce nie ma żadnych zadań oczekujących na uruchomienie ('queued') dla zadanych kryteriów.")
            job_prog.empty()
            job_status.empty()
        else:
            job_prog.empty()
            job_status.empty()
            if st.button("Odśwież Listę Zadań poniżej"):
                st.rerun()

    st.markdown("---")
    
    # -------------------------------------------------------------
    # WIZUALIZACJA ZADAŃ
    # -------------------------------------------------------------
    if not jobs:
        st.info("Brak zadań w bazie spełniających Twoje filtry.")
        return
        
    st.subheader(f"Lista Zadań ({len(jobs)})")
    
    for job in jobs:
        color = "🔵" # queued
        if job["status"] == "completed": color = "🟢"
        elif job["status"] == "failed": color = "🔴"
        elif job["status"] == "processing": color = "🟡"
        elif job["status"] == "draft": color = "⚪"
        
        with st.expander(f"{color} Słowo: {job['main_keyword']} | Typ: {job['content_type']} | Status: {job['status'].upper()} | Kampania: {camp_options.get(job['campaign_id'], 'Nieznana')}"):
            c1, c2, c3 = st.columns([2, 1, 1])
            with c1:
                st.markdown(f"**ID:** `{job['id']}`")
                st.markdown(f"**Język:** `{job['language']}` (`{job['locale']}`)")
                st.markdown(f"**Model AI:** `{job['provider']} ({job['model']})`")
                if job.get("current_step_key"):
                    st.caption(f"Ostatni wykonywany krok: `{job['current_step_key']}`")
                if job.get("error_message"):
                    st.error(f"Komunikat Błędu: {job['error_message']}")
            
            with c2:
                st.write("**Akcje Generowania**")
                if job["status"] not in ["completed", "processing"]:
                    if st.button("▶️ Uruchom to zadanie", key=f"run_{job['id']}", use_container_width=True):
                        _run_job_ui(job['id'])
                
                if job["status"] in ["failed", "draft"]:
                    if st.button("🔄 Wrzuć do 'Queued'", key=f"que_{job['id']}", type="secondary", use_container_width=True):
                        update_job_status(job["id"], "queued")
                        st.rerun()
                        
            with c3:
                st.write("**Zarządzanie**")
                if job["status"] not in ["completed", "failed"]:
                    if st.button("❌ Anuluj / Failed", key=f"fail_{job['id']}", type="secondary", use_container_width=True):
                        update_job_status(job["id"], "failed", "Zadanie ręcznie anulowane przez operatora.")
                        st.rerun()
                        
                if job["status"] == "completed":
                    st.success("Zadanie zakończone pomyślnie. (Moduł Wyników)")


def _run_job_ui(job_id):
    """Metoda UI dedykowana do uruchomienia pojedynczego rekordu z listy expanderów."""
    st.markdown("---")
    st.markdown(f"### ⚙️ Przetwarzanie zadania: `{job_id}`")
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    def on_progress(step_name, current, total):
        pct = min(100, int((current / total) * 100)) if total > 0 else 100
        progress_bar.progress(pct)
        status_text.info(f"Oczekuję na AI w etapie: **{step_name}** ({current+1} / {total})")
        
    with st.spinner("AI przetwarza kroki. Proszę nie odświeżać karty przeglądarki..."):
        from services.job_processor import process_single_job
        success, msg = process_single_job(job_id, on_progress)
        
    if success:
        progress_bar.progress(100)
        status_text.success(f"Ukończono sukcesem! {msg}", icon="✅")
    else:
        status_text.error(f"Proces przerwany: {msg}", icon="🚨")
        
    if st.button("🔄 Odśwież widok", type="primary"):
        st.rerun()
