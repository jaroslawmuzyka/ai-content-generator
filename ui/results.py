import streamlit as st
import json
from services.job_repository import get_content_jobs, get_job_steps, update_job_status, update_job_final_fields, duplicate_job
from services.campaign_service import get_campaigns

from utils.constants import JOB_STATUSES

def render():
    st.title("✅ Wyniki treści")
    st.write("Tutaj sprawdzisz finalną treść, wyniki etapów, SEO QA i ocenę atrakcyjności tekstu.")

    # ------------------------------------------------------------------
    # FILTRY
    # ------------------------------------------------------------------
    all_camps = get_campaigns("all")
    camp_options = {"all": "Wszystkie kampanie"}
    for c in all_camps:
        camp_options[c["id"]] = c["name"]

    fc1, fc2, fc3, fc4 = st.columns(4)
    f_camp = fc1.selectbox("Kampania", list(camp_options.keys()), format_func=lambda x: camp_options[x], key="res_f_camp")
    f_status = fc2.selectbox(
        "Status",
        JOB_STATUSES,
        index=JOB_STATUSES.index("completed"),
        key="res_f_status"
    )
    f_ctype = fc3.selectbox("Typ treści", ["all", "ecommerce_category", "ecommerce_product", "blog_post", "landing_page"], key="res_f_ctype")
    f_lang = fc4.selectbox("Język", ["all", "pl", "en", "de", "cs", "sk"], key="res_f_lang")

    f_keyword = st.text_input("🔍 Szukaj po frazie kluczowej:", placeholder="Wpisz fragment frazy...")

    jobs = get_content_jobs(
        campaign_id=f_camp if f_camp != "all" else None,
        status=f_status if f_status != "all" else None,
        content_type=f_ctype if f_ctype != "all" else None,
        language=f_lang if f_lang != "all" else None,
        search_keyword=f_keyword if f_keyword else None
    )

    if not jobs:
        st.info("ℹ️ Nie ma jeszcze wygenerowanych wyników. Przejdź do kolejki i uruchom generowanie.")
        return

    st.divider()

    # ------------------------------------------------------------------
    # WYBÓR ZADANIA
    # ------------------------------------------------------------------
    st.subheader(f"Wybierz zadanie do podglądu ({len(jobs)} wyników)")

    job_opts = {
        j["id"]: f"[{j['status'].upper()}] {j['main_keyword']} · {j['content_type']} · {j['created_at'][:16].replace('T', ' ')}"
        for j in jobs
    }
    selected_job_id = st.selectbox("Lista zadań:", list(job_opts.keys()), format_func=lambda x: job_opts[x])

    job = next((j for j in jobs if j["id"] == selected_job_id), None)
    if not job:
        return

    st.markdown("---")

    # ------------------------------------------------------------------
    # ZARZĄDZANIE STATUSEM (nad tabami)
    # ------------------------------------------------------------------
    act1, act2, act3, act4 = st.columns(4)
    if act1.button("👁️ Needs Review", use_container_width=True, help="Oznacz jako wymagający manualnej weryfikacji."):
        update_job_status(selected_job_id, "needs_review")
        st.rerun()
    if act2.button("✅ Zatwierdź (Completed)", use_container_width=True, type="primary", help="Zatwierdź tekst — będzie widoczny w Eksporcie."):
        update_job_status(selected_job_id, "completed")
        st.rerun()
    if act3.button("🔄 Duplikuj jako nowe", use_container_width=True, help="Klonuje zadanie (te same parametry, status Draft)."):
        new_id = duplicate_job(selected_job_id)
        if new_id:
            st.success("Zadanie zduplikowane! Znajdziesz je w Kolejce ze statusem Draft.")
        else:
            st.error("Nie udało się zduplikować zadania.")
    act4.write(f"**Status:** {job.get('status','?').upper()}")

    st.markdown("---")

    # ------------------------------------------------------------------
    # GŁÓWNE TABY
    # ------------------------------------------------------------------
    tab_content, tab_seo, tab_attr, tab_steps, tab_prompts, tab_input = st.tabs([
        "📄 Finalna treść",
        "🔍 SEO",
        "✨ Atrakcyjność",
        "🔧 Etapy AI",
        "📋 Użyte prompty",
        "📥 Dane wejściowe"
    ])

    # ==========================================
    # TAB 1: FINALNA TREŚĆ
    # ==========================================
    with tab_content:
        st.subheader("Edycja i podgląd wygenerowanej treści")

        view_mode = st.radio("Tryb widoku:", ["✏️ Edycja (kod HTML)", "👁️ Podgląd renderowany"], horizontal=True)

        with st.form("edit_results_form", border=False):
            c_meta1, c_meta2 = st.columns(2)
            meta_title = c_meta1.text_input(
                "Meta Title",
                value=job.get("meta_title") or "",
                help="Maks. 60 znaków. Pojawia się w wynikach Google jako niebieski link."
            )
            char_title = len(meta_title)
            c_meta1.caption(f"{'✅' if char_title <= 60 else '⚠️'} {char_title}/60 znaków")

            meta_desc = c_meta2.text_area(
                "Meta Description",
                value=job.get("meta_description") or "",
                height=100,
                help="Maks. 160 znaków. Krótki opis strony widoczny pod tytułem w Google."
            )
            char_desc = len(meta_desc)
            c_meta2.caption(f"{'✅' if char_desc <= 160 else '⚠️'} {char_desc}/160 znaków")

            st.markdown("---")
            st.markdown("##### 📄 Treść główna artykułu")
            st.caption("Sekcje H2 + akapity wygenerowane przez pipeline. Nie zawiera FAQ.")

            if view_mode == "✏️ Edycja (kod HTML)":
                final_html = st.text_area(
                    "Treść HTML (bez FAQ)",
                    value=job.get("final_html") or "",
                    height=400,
                    help="Główna treść strony. FAQ jest w osobnym polu poniżej."
                )
            else:
                final_html = job.get("final_html") or ""
                safe_html = final_html.replace("<script", "&lt;script").replace("</script>", "&lt;/script&gt;")
                st.markdown("**Pogląd głównej treści:**")
                st.markdown(f"<h2>{meta_title or 'Brak Meta Title'}</h2><em>{meta_desc or 'Brak Meta Description'}</em><hr>", unsafe_allow_html=True)
                st.markdown(safe_html, unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("##### ❓ Sekcja FAQ")
            st.caption("FAQ generowane niezależnie przez dedykowany krok AI. W CMS wkleja się po głównej treści.")

            faq_html = st.text_area(
                "FAQ HTML (osobne pole)",
                value=job.get("faq_html") or "",
                height=200,
                help="Sekcja FAQ — przechowywana osobno od treści głównej. Obsługuje rich snippets Google."
            )

            if view_mode == "👁️ Pogląd renderowany" and (job.get("faq_html") or "").strip():
                safe_faq = (job.get("faq_html") or "").replace("<script", "&lt;script").replace("</script>", "&lt;/script&gt;")
                st.markdown("**Pogląd FAQ:**")
                st.markdown(safe_faq, unsafe_allow_html=True)

            if st.form_submit_button("💾 Zapisz zmiany", type="primary"):
                if update_job_final_fields(selected_job_id, final_html, meta_title, meta_desc, faq_html):
                    st.success("✅ Zmiany zapisane!")
                    st.rerun()
                else:
                    st.error("❌ Nie udało się zapisać. Sprawdź połączenie z bazą danych.")

    # ==========================================
    # TAB 2: SEO QA
    # ==========================================
    with tab_seo:
        st.subheader("Automatyczne QA SEO")

        seo_report = job.get("seo_report_json")
        if not seo_report:
            st.info("ℹ️ Brak raportu SEO dla tego zadania. Raport generowany jest automatycznie przez etap `seo_qa`.")
        else:
            qa = seo_report.get("rules_qa", {})
            ai_qa = seo_report.get("ai_report")

            if qa.get("is_empty"):
                st.error("🚨 Finalny HTML jest pusty! Zadanie nie wygenerowało treści.")
            else:
                if qa.get("is_markdown"):
                    st.warning("⚠️ Wykryto znaczniki Markdown (`#`, `**`). Model zwrócił tekst zamiast HTML — sprawdź krok `html_cleanup`.")

                # Metryki
                m1, m2, m3, m4 = st.columns(4)

                l_diff = qa.get("length_diff", 0)
                diff_str = (f"+{l_diff}" if l_diff > 0 else str(l_diff)) if l_diff != 0 else ""
                if qa.get("target_length") == 0:
                    diff_str = "(Bez limitu)"
                m1.metric("Długość (znaki)", qa.get("char_count", 0), diff_str)
                m2.metric("Główna fraza (wystąpienia)", qa.get("main_keyword_count", 0))
                m3.metric("Nagłówek H1", "TAK ✅" if qa.get("has_h1") else "NIE ❌")
                m4.metric("Liczba nagłówków H2", qa.get("h2_count", 0))

                # Frazy
                used = qa.get("secondary_keywords_used", [])
                missing = qa.get("secondary_keywords_missing", [])

                if used:
                    st.success(f"✅ Użyte frazy poboczne: {', '.join(used)}")
                if missing:
                    st.warning(f"⚠️ Nieużyte frazy poboczne: {', '.join(missing)}")

                # HTML clean
                if qa.get("contains_forbidden_tags") or qa.get("contains_forbidden_attrs"):
                    st.error(
                        f"🧹 Cleaner HTML usunął niedozwolone elementy:\n"
                        f"Tagi: {qa.get('forbidden_tags_list')} | Atrybuty: {qa.get('forbidden_attrs_list')}"
                    )
                else:
                    st.success("✅ HTML był strukturalnie poprawny — brak interwencji cleanera.")

            if ai_qa:
                with st.expander("📝 Pełny raport AI (krok seo_qa)"):
                    st.json(ai_qa)

    # ==========================================
    # TAB 3: ATRAKCYJNOŚĆ
    # ==========================================
    with tab_attr:
        st.subheader("Ocena Atrakcyjności i Skuteczności Marketingowej")

        attr_score = job.get("attractiveness_score")
        if attr_score is not None:
            score_color = "🟢" if attr_score >= 7 else ("🟡" if attr_score >= 5 else "🔴")
            st.metric("Ogólna ocena marketingowa", f"{score_color} {attr_score}/10")
        else:
            st.info("ℹ️ Brak oceny atrakcyjności. Zadanie wygenerowano w trybie SEO-only lub bez etapu `attractiveness_qa`.")

        attr_report = job.get("attractiveness_report_json")
        if attr_report:
            rules_qa = attr_report.get("rules_qa", {})
            ai_report = attr_report.get("ai_report", {})

            col_r1, col_r2 = st.columns(2)

            with col_r1:
                st.markdown("#### 📣 Reguły marketingowe")
                has_cta = rules_qa.get("has_cta")
                st.metric("Call To Action wykryty", "✅ TAK" if has_cta else "❌ NIE")

                generic_found = rules_qa.get("generic_phrases_found", [])
                if generic_found:
                    st.warning(f"⚠️ Wykryto puste ogólniki AI: {', '.join(generic_found)}")
                else:
                    st.success("✅ Brak pustych ogólników i klisz AI.")

                forbidden = rules_qa.get("forbidden_phrases_found", [])
                if forbidden:
                    st.error(f"🚫 Zakazane frazy w tekście: {', '.join(forbidden)}")

                required_missing = rules_qa.get("required_phrases_missing", [])
                if required_missing:
                    st.warning(f"⚠️ Brakuje wymaganych fraz: {', '.join(required_missing)}")

            with col_r2:
                st.markdown("#### 🤖 Ocena AI")
                if ai_report:
                    if isinstance(ai_report, dict):
                        strengths = ai_report.get("mocne_strony") or ai_report.get("strengths")
                        weaknesses = ai_report.get("slabe_strony") or ai_report.get("weaknesses")
                        recs = ai_report.get("rekomendacje") or ai_report.get("recommendations")

                        if strengths:
                            st.markdown("**Mocne strony:**")
                            if isinstance(strengths, list):
                                for s in strengths:
                                    st.markdown(f"- {s}")
                            else:
                                st.write(strengths)

                        if weaknesses:
                            st.markdown("**Słabe strony:**")
                            if isinstance(weaknesses, list):
                                for w in weaknesses:
                                    st.markdown(f"- {w}")
                            else:
                                st.write(weaknesses)

                        if recs:
                            st.markdown("**Rekomendacje:**")
                            if isinstance(recs, list):
                                for r in recs:
                                    st.markdown(f"- {r}")
                            else:
                                st.write(recs)
                    else:
                        st.write(ai_report)

                    with st.expander("🔍 Pełny JSON raportu AI"):
                        st.json(ai_report)

    # ==========================================
    # TAB 4: ETAPY AI
    # ==========================================
    with tab_steps:
        st.subheader("Historia kroków AI")

        steps = get_job_steps(selected_job_id)
        if not steps:
            st.info("ℹ️ Brak historii kroków dla tego zadania.")
        else:
            total_in = sum(s.get("input_tokens") or 0 for s in steps)
            total_out = sum(s.get("output_tokens") or 0 for s in steps)
            tk1, tk2 = st.columns(2)
            tk1.metric("Tokeny wejściowe (kontekst)", total_in)
            tk2.metric("Tokeny wyjściowe (odpowiedzi AI)", total_out)

            st.divider()

            for s in steps:
                status = s.get("status", "")
                icon = "✅" if status == "completed" else ("❌" if status == "failed" else ("⏭️" if status == "skipped" else "⏳"))

                with st.expander(f"{icon} Krok {s['step_order']}: {s['step_name']} | {s.get('provider','?')} / {s.get('model','?')}"):
                    st.caption(f"Status: **{status.upper()}** | Tokeny: IN `{s.get('input_tokens',0)}` / OUT `{s.get('output_tokens',0)}`")

                    if s.get("error_message"):
                        st.error(f"**Błąd AI:** {s['error_message']}")

                    st.markdown("**Output (odpowiedź AI):**")
                    st.text_area(
                        "Output",
                        value=s.get("output_text") or "",
                        height=200,
                        key=f"out_{s['id']}",
                        disabled=True,
                        label_visibility="collapsed"
                    )
                    if s.get("output_json"):
                        with st.expander("🔍 Sparsowany JSON"):
                            st.json(s["output_json"])

    # ==========================================
    # TAB 5: UŻYTE PROMPTY
    # ==========================================
    with tab_prompts:
        st.subheader("Prompty użyte przy generowaniu")
        st.caption("Dokładne instrukcje wysłane do AI w momencie generowania (snapshoty — niezmienne po zapisaniu zadania).")

        steps = get_job_steps(selected_job_id)
        if not steps:
            st.info("ℹ️ Brak zapisanych kroków dla tego zadania.")
        else:
            for s in steps:
                with st.expander(f"Krok {s['step_order']}: {s['step_name']}"):
                    st.markdown("**System Prompt:**")
                    st.code(s.get("system_prompt_used") or "(Brak)", language=None)
                    st.markdown("**User Prompt (z podmienionymi zmiennymi):**")
                    st.code(s.get("user_prompt_used") or "(Brak)", language=None)

    # ==========================================
    # TAB 6: DANE WEJŚCIOWE
    # ==========================================
    with tab_input:
        st.subheader("Parametry wejściowe zadania")

        d1, d2 = st.columns(2)
        with d1:
            st.write(f"**Data zlecenia:** `{job.get('created_at','?')[:16].replace('T',' ')}`")
            st.write(f"**Operator:** `{job.get('operator_name','?')}`")
            st.write(f"**Fraza główna:** `{job.get('main_keyword','?')}`")
            st.write(f"**Frazy poboczne:** `{job.get('secondary_keywords') or '(Brak)'}`")
            st.write(f"**Tryb generowania:** `{job.get('generation_mode','?')}`")
        with d2:
            st.write(f"**URL:** `{job.get('url') or '(Brak)'}`")
            st.write(f"**Docelowa długość:** `{job.get('target_length') or 'Dowolna'}`")
            st.write(f"**Język / Locale:** `{job.get('language')} / {job.get('locale')}`")
            st.write(f"**Model AI:** `{job.get('provider')} / {job.get('model')}`")

        if job.get("additional_notes"):
            st.markdown("**Dodatkowe wytyczne operatora:**")
            st.info(job["additional_notes"])

        if job.get("current_content"):
            with st.expander("📄 Istniejąca treść (do rewrite)"):
                st.text(job["current_content"])
