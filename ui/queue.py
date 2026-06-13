import streamlit as st
import pandas as pd
from services.job_repository import get_content_jobs, update_job_status, requeue_failed_jobs
from services.job_processor import process_single_job, process_job_batch
from services.campaign_service import get_campaigns
from services.dashboard_service import restore_interrupted_jobs
from db.supabase_client import get_supabase_client

STATUS_CONFIG = {
    "queued":       {"icon": "🔵", "label": "W kolejce"},
    "processing":   {"icon": "🟡", "label": "Przetwarzane"},
    "completed":    {"icon": "🟢", "label": "Gotowe"},
    "failed":       {"icon": "🔴", "label": "Błąd"},
    "draft":        {"icon": "⚪", "label": "Szkic"},
    "needs_review": {"icon": "🟠", "label": "Do przeglądu"},
    "interrupted":  {"icon": "🛑", "label": "Przerwane"},
}

def _status_badge(status: str) -> str:
    cfg = STATUS_CONFIG.get(status, {"icon": "❓", "label": status})
    return f"{cfg['icon']} {cfg['label']}"

def render():
    st.title("⚙️ Kolejka generowania")
    st.write("Tutaj uruchamiasz generowanie treści. Na darmowym Streamlit przetwarzanie działa w aktywnej sesji, dlatego zalecane są małe partie.")

    # ------------------------------------------------------------------
    # PANEL SZYBKICH AKCJI
    # ------------------------------------------------------------------
    all_camps = get_campaigns("all")
    camp_options = {"all": "Wszystkie kampanie"}
    for c in all_camps:
        camp_options[c["id"]] = c["name"]

    st.markdown("### ▶️ Przetwarzanie partii")
    st.caption("Uruchamia kolejno zadania o statusie **Queued**. Nie zamykaj karty przeglądarki podczas generowania!")

    ba1, ba2, ba3, ba4, ba5, ba6 = st.columns([2, 1, 1, 1, 1, 1])
    batch_camp = ba1.selectbox(
        "Kampania:",
        list(camp_options.keys()),
        format_func=lambda x: camp_options[x],
        label_visibility="collapsed"
    )

    col_limit = None
    if ba2.button("▶ 1 zadanie", use_container_width=True):
        col_limit = 1
        st.session_state["start_batch"] = True
        st.session_state["batch_limit"] = 1
    if ba3.button("▶ 5 zadań", use_container_width=True):
        st.session_state["start_batch"] = True
        st.session_state["batch_limit"] = 5
    if ba4.button("▶ 10 zadań", type="primary", use_container_width=True):
        st.session_state["start_batch"] = True
        st.session_state["batch_limit"] = 10
    if ba5.button("🔄 Ponów błędne", use_container_width=True, help="Zmienia status zadań 'failed' z powrotem na 'queued'."):
        count = requeue_failed_jobs(batch_camp if batch_camp != "all" else None)
        st.success(f"✅ {count} zadań oznaczono ponownie jako 'queued'.")
        st.rerun()
    if ba6.button("🔓 Odblokuj przerwane", use_container_width=True, help="Przywraca zadania ze statusem 'interrupted' do kolejki."):
        count = restore_interrupted_jobs()
        st.success(f"✅ Odblokowano {count} zadań.")
        st.rerun()

    # Duża partia — ostrzeżenie
    if st.session_state.get("show_all_warning"):
        st.warning(
            "⚠️ **Uwaga:** Przetwarzanie wszystkich zadań naraz bez workera w tle może spowodować "
            "timeout Streamlit i zawiesić zadania. Zalecane jest uruchamianie po 5–10 naraz."
        )
        wc1, wc2 = st.columns([1, 5])
        if wc1.button("Tak, rozumiem ryzyko", type="primary"):
            st.session_state["start_batch"] = True
            st.session_state["batch_limit"] = 0
            st.session_state["show_all_warning"] = False
            st.rerun()
        if wc2.button("Anuluj"):
            st.session_state["show_all_warning"] = False
            st.rerun()

    # ------------------------------------------------------------------
    # URUCHOMIENIE BATCHA
    # ------------------------------------------------------------------
    if st.session_state.get("start_batch"):
        st.session_state["start_batch"] = False

        batch_limit_val = st.session_state.get("batch_limit")
        limit_val = None if batch_limit_val == 0 else batch_limit_val
        c_id_val = batch_camp if batch_camp != "all" else None

        st.markdown("---")
        st.markdown("### ⚙️ Generowanie w toku...")

        batch_prog = st.progress(0)
        batch_status = st.empty()
        job_prog = st.progress(0)
        job_status = st.empty()

        def on_batch(idx, total, job, successes, errors):
            pct = int((idx / total) * 100) if total > 0 else 100
            batch_prog.progress(pct)
            if job:
                batch_status.markdown(
                    f"**Partia ({idx+1}/{total})** | Fraza: `{job['main_keyword']}` | "
                    f"✅ Sukces: `{successes}` | ❌ Błędy: `{errors}`"
                )
            else:
                batch_status.success(f"✅ Koniec! Przetworzono {total} zadań (✅ {successes} | ❌ {errors})")

        def on_job(step_name, current, total):
            pct = min(100, int((current / total) * 100)) if total > 0 else 100
            job_prog.progress(pct)
            job_status.info(f"Etap: **{step_name}** ({current+1}/{total})")

        with st.spinner("AI pracuje... Nie zamykaj tej karty przeglądarki."):
            total_ran, ok_cnt, err_cnt = process_job_batch(limit_val, c_id_val, on_batch, on_job)

        if total_ran == 0:
            st.info("ℹ️ Brak zadań w kolejce (status 'queued') dla wybranych kryteriów.")
            job_prog.empty()
            job_status.empty()
        else:
            job_prog.empty()
            job_status.empty()
            if st.button("🔄 Odśwież listę zadań", type="primary"):
                st.rerun()

    st.divider()

    # ------------------------------------------------------------------
    # FILTRY I LISTA ZADAŃ
    # ------------------------------------------------------------------
    st.markdown("### 📋 Lista zadań")

    fc1, fc2, fc3, fc4 = st.columns(4)
    f_camp = fc1.selectbox("Kampania", list(camp_options.keys()), format_func=lambda x: camp_options[x], key="q_f_camp")
    f_status = fc2.selectbox("Status", ["all", "queued", "processing", "completed", "failed", "draft", "needs_review", "interrupted"], key="q_f_status")
    f_ctype = fc3.selectbox("Typ treści", ["all", "ecommerce_category", "ecommerce_product", "blog_post", "landing_page"], key="q_f_ctype")
    f_lang = fc4.selectbox("Język", ["all", "pl", "en", "de", "cs", "sk"], key="q_f_lang")

    jobs = get_content_jobs(
        campaign_id=f_camp if f_camp != "all" else None,
        status=f_status if f_status != "all" else None,
        content_type=f_ctype if f_ctype != "all" else None,
        language=f_lang if f_lang != "all" else None
    )

    if not jobs:
        st.info("ℹ️ Nie ma jeszcze zadań w tej kampanii. Dodaj pojedynczą treść lub zaimportuj plik XLSX.")
        return

    st.caption(f"Znaleziono **{len(jobs)}** zadań.")

    # Renderowanie listy jako expandery z akcjami
    for job in jobs:
        status = job.get("status", "draft")
        badge = _status_badge(status)
        camp_name = camp_options.get(job.get("campaign_id"), "Nieznana kampania")

        expander_label = f"{badge} | **{job['main_keyword']}** | {camp_name} | {job.get('content_type','?')} | {job.get('language','?')} | {job.get('created_at','')[:10]}"

        with st.expander(expander_label):
            info_col, action_col1, action_col2 = st.columns([3, 1, 1])

            with info_col:
                st.write(f"**Model AI:** `{job.get('provider')} / {job.get('model')}`")
                st.write(f"**Operator:** `{job.get('operator_name', 'N/A')}`")
                if job.get("current_step_key"):
                    st.caption(f"Ostatni etap: `{job['current_step_key']}`")
                if job.get("error_message"):
                    st.error(f"**Błąd:** {job['error_message']}")

            with action_col1:
                st.write("**Generowanie**")
                if status not in ["completed", "processing"]:
                    if st.button("▶️ Uruchom", key=f"run_{job['id']}", use_container_width=True, type="primary"):
                        _run_single_job_ui(job["id"])
                    if st.button("🧪 Test", key=f"test_{job['id']}", use_container_width=True):
                        _run_test_job_ui(job["id"], job)
                if status in ["failed", "draft", "interrupted"]:
                    if st.button("🔄 → Queued", key=f"que_{job['id']}", use_container_width=True):
                        update_job_status(job["id"], "queued")
                        st.rerun()

            with action_col2:
                st.write("**Zarządzanie**")
                if status not in ["completed", "failed"]:
                    # Zmienione "Anuluj" – jeśli status to "processing", wymusza reset do "queued" jako obejście
                    if status == "processing":
                        if st.button("❌ Zresetuj zawieszone", key=f"reset_{job['id']}", use_container_width=True):
                            update_job_status(job["id"], "queued", "Zadanie zresetowane przez operatora.")
                            st.rerun()
                    else:
                        if st.button("❌ Anuluj", key=f"fail_{job['id']}", use_container_width=True):
                            update_job_status(job["id"], "failed", "Zadanie ręcznie anulowane przez operatora.")
                            st.rerun()
                if status == "completed":
                    st.success("Gotowe ✅")


def _run_single_job_ui(job_id):
    """Uruchamia pojedyncze zadanie z widoku listy i pokazuje postęp na żywo w panelach."""
    st.markdown(f"### ⚙️ Przetwarzam zadanie `{job_id}`")

    progress_bar = st.progress(0)
    status_text = st.empty()
    
    logs_container = st.container()
    completed_steps_keys = set()
    from db.supabase_client import get_supabase_client
    client = get_supabase_client()

    def on_progress(step_name, current, total):
        pct = min(100, int((current / total) * 100)) if total > 0 else 100
        progress_bar.progress(pct)
        status_text.info(f"Etap: **{step_name}** ({current+1}/{total})")
        
        # Pobierz logi dotychczas wykonanych kroków z bazy
        res = client.table("content_job_steps").select("*").eq("job_id", job_id).order("step_order").execute()
        for s in res.data:
            if s["status"] == "completed" and s["step_key"] not in completed_steps_keys:
                completed_steps_keys.add(s["step_key"])
                with logs_container.expander(f"✅ Etap {s['step_order']}: {s['step_name']} | {s.get('provider')}/{s.get('model')}"):
                    out = str(s.get('output_text', ''))
                    st.caption(f"Status: {s.get('status')} | Zakończono: {s.get('completed_at', '')[:19]}")
                    st.markdown("**Output Preview:**")
                    st.text(out[:800] + ("..." if len(out) > 800 else ""))

    with st.spinner("AI generuje treść... Proszę nie odświeżać strony."):
        success, msg = process_single_job(job_id, on_progress)

    if success:
        progress_bar.progress(100)
        status_text.success(f"✅ Zadanie ukończone! {msg}")
    else:
        status_text.error(f"❌ Błąd podczas generowania: {msg}")

    if st.button("🔄 Odśwież widok", type="primary", key=f"refresh_after_{job_id}"):
        st.rerun()

def _run_test_job_ui(job_id, job_data):
    """Tryb testowy z wylistowaniem szczegółowych logów."""
    st.markdown(f"### 🧪 Test generowania: `{job_data.get('main_keyword', job_id)}`")
    st.warning("⚠️ **Test generowania** uruchamia zapytania do modelu AI i może generować koszt API. Na początek użyj tańszego modelu.")
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Kontener na logi poszczególnych etapów
    logs_container = st.container()
    completed_steps_keys = set()
    client = get_supabase_client()
    
    def on_progress(step_name, current, total):
        pct = min(100, int((current / total) * 100)) if total > 0 else 100
        progress_bar.progress(pct)
        status_text.info(f"Etap: **{step_name}** ({current+1}/{total})")
        
        # Pobierz logi dotychczas wykonanych kroków z bazy
        res = client.table("content_job_steps").select("*").eq("job_id", job_id).order("step_order").execute()
        for s in res.data:
            if s["status"] == "completed" and s["step_key"] not in completed_steps_keys:
                completed_steps_keys.add(s["step_key"])
                with logs_container.expander(f"✅ Etap {s['step_order']}: {s['step_name']} | {s.get('provider')}/{s.get('model')}"):
                    out = str(s.get('output_text', ''))
                    st.caption(f"Status: {s.get('status')} | Zakończono: {s.get('completed_at', '')[:19]}")
                    st.markdown("**Output Preview:**")
                    st.text(out[:500] + ("..." if len(out) > 500 else ""))

    with st.spinner("AI generuje treść... Trwa test."):
        success, msg = process_single_job(job_id, on_progress)

    # Jeden ostatni rzut po zakończeniu, aby pobrać ostatnie kroki i błędy
    res = client.table("content_job_steps").select("*").eq("job_id", job_id).order("step_order").execute()
    error_count = 0
    for s in res.data:
        if s.get("status") == "failed":
            error_count += 1
        if s["status"] in ["completed", "failed"] and s["step_key"] not in completed_steps_keys:
            completed_steps_keys.add(s["step_key"])
            icon = "✅" if s["status"] == "completed" else "❌"
            with logs_container.expander(f"{icon} Etap {s['step_order']}: {s['step_name']} | {s.get('provider')}/{s.get('model')}"):
                out = str(s.get('output_text', ''))
                err = str(s.get('error_message', ''))
                st.caption(f"Status: {s.get('status')} | Zakończono: {str(s.get('completed_at', ''))[:19]}")
                if err:
                    st.error(f"Błąd: {err}")
                st.markdown("**Output Preview:**")
                st.text(out[:500] + ("..." if len(out) > 500 else ""))

    if success:
        progress_bar.progress(100)
        status_text.success("✅ Test zakończony pomyślnie!")
        
        final_job = client.table("content_jobs").select("*").eq("id", job_id).execute().data[0]
        
        st.markdown("### 📊 Podsumowanie Testu")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Status", "Gotowe")
        c2.metric("Etapów AI", len(completed_steps_keys))
        c3.metric("Błędy", error_count)
        c4.metric("Długość HTML", len(final_job.get("final_html") or ""))
        
        seo_report = final_job.get("seo_report_json", {})
        attr_report = final_job.get("attractiveness_report_json", {})
        
        sc1, sc2 = st.columns(2)
        if isinstance(seo_report, dict) and "ai_report" in seo_report and isinstance(seo_report["ai_report"], dict):
            sc1.metric("SEO Score", f"{seo_report['ai_report'].get('overall_score', '?')}/10")
        if isinstance(attr_report, dict) and "ai_report" in attr_report and isinstance(attr_report["ai_report"], dict):
            sc2.metric("Attractiveness Score", f"{attr_report['ai_report'].get('overall_score', '?')}/10")
            
    else:
        status_text.error(f"❌ Test przerwany błędem: {msg}")

    if st.button("🔄 Zamknij i odśwież widok", type="primary", key=f"refresh_after_test_{job_id}"):
        st.rerun()
