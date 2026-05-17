import streamlit as st
import json
from services.job_repository import get_content_jobs, get_job_steps, update_job_status, update_job_final_fields, duplicate_job
from utils.constants import JOB_STATUSES
from services.campaign_service import get_campaigns

def render():
    st.title("Wyniki i Edycja")
    st.write("Podgląd, weryfikacja i edycja wygenerowanych treści gotowych do publikacji.")
    
    # ------------------------------------------------------------------
    # GŁÓWNE FILTRY WYSZUKIWANIA
    # ------------------------------------------------------------------
    all_camps = get_campaigns("all")
    camp_options = {"all": "Wszystkie kampanie"}
    for c in all_camps: camp_options[c["id"]] = c["name"]
        
    c1, c2, c3, c4 = st.columns(4)
    f_camp = c1.selectbox("Wybierz kampanię", list(camp_options.keys()), format_func=lambda x: camp_options[x], key="res_f_camp")
    
    # Domyślnie na "completed" by nie czytać śmieci
    f_status = c2.selectbox("Filtruj status", JOB_STATUSES, index=JOB_STATUSES.index("completed") if "completed" in JOB_STATUSES else 0, key="res_f_status")
    f_ctype = c3.selectbox("Typ treści", ["all", "ecommerce_category", "ecommerce_product", "blog_post", "landing_page"], key="res_f_ctype")
    f_lang = c4.selectbox("Język", ["all", "pl", "en", "de", "cs", "sk"], key="res_f_lang")
    
    f_keyword = st.text_input("🔍 Szukaj po głównej frazie kluczowej (main_keyword):", placeholder="Wpisz fragment frazy...")
    
    jobs = get_content_jobs(
        campaign_id=f_camp if f_camp != "all" else None,
        status=f_status if f_status != "all" else None,
        content_type=f_ctype if f_ctype != "all" else None,
        language=f_lang if f_lang != "all" else None,
        search_keyword=f_keyword if f_keyword else None
    )
    
    if not jobs:
        st.info("Brak zadań spełniających podane kryteria. Pamiętaj, że domyślnie wyświetlane są tylko zadania ukończone ('completed').")
        return
        
    st.divider()
    
    # ------------------------------------------------------------------
    # WYBÓR KONKRETNEGO ZADANIA
    # ------------------------------------------------------------------
    st.subheader("Wybór zadania do podglądu")
    
    # Tworzymy czytelną listę do selectboxa z identyfikacją zadania
    job_opts = {j["id"]: f"[{j['status'].upper()}] {j['main_keyword']} (Typ: {j['content_type']}) - {j['created_at'][:10]}" for j in jobs}
    selected_job_id = st.selectbox("Lista dostępnych zadań:", list(job_opts.keys()), format_func=lambda x: job_opts[x])
    
    job = next(j for j in jobs if j["id"] == selected_job_id)
    if not job: return
        
    st.markdown("---")
    
    # ------------------------------------------------------------------
    # PANELE GŁÓWNE
    # ------------------------------------------------------------------
    tab1, tab2, tab3, tab4 = st.tabs(["📝 Wyniki i Korekta", "👁️ Podgląd Wyglądu", "🎯 Skuteczność (Atrakcyjność)", "🕰️ Historia i Logi AI"])
    
    # TAB 1: Edycja surowego kodu HTML i Metadanych
    with tab1:
        st.subheader("Edycja manualna i zatwierdzanie")
        
        with st.form("edit_results_form", border=False):
            final_html = st.text_area("Final HTML (Kod źródłowy)", value=job.get("final_html") or "", height=400, help="Główna wygenerowana treść od AI oczyszczona z błędnych tagów.")
            
            c_meta1, c_meta2 = st.columns(2)
            meta_title = c_meta1.text_input("Meta Title", value=job.get("meta_title") or "")
            meta_desc = c_meta2.text_area("Meta Description", value=job.get("meta_description") or "", height=100)
            
            faq_html = st.text_area("FAQ (Sekcja Pytań i Odpowiedzi - Opcjonalnie)", value=job.get("faq_html") or "", height=200)
            
            st.divider()
            submit_edits = st.form_submit_button("💾 Zapisz poprawki bezpośrednio do bazy", type="primary")
            
            if submit_edits:
                if update_job_final_fields(selected_job_id, final_html, meta_title, meta_desc, faq_html):
                    st.success("Zapisano zmiany w ostatecznych wynikach rekordu!")
                    st.rerun()
                    
        st.markdown("### Zarządzanie stanem i cyklem życia zadania")
        c_a1, c_a2, c_a3 = st.columns(3)
        if c_a1.button("👁️ Oznacz jako Needs Review", use_container_width=True, help="Jeśli treść wymaga opinii eksperta SEO / Copywritera."):
            update_job_status(selected_job_id, "needs_review")
            st.rerun()
            
        if c_a2.button("✅ Oznacz jako Completed", use_container_width=True, help="Potwierdzasz poprawność. Czeka tylko na Eksport."):
            update_job_status(selected_job_id, "completed")
            st.rerun()
            
        if c_a3.button("🔄 Duplikuj jako Nowe Zadanie", use_container_width=True, help="Klonuje to samo słowo, prompt itp., od zera do statusu DRAFT."):
            new_id = duplicate_job(selected_job_id)
            if new_id:
                st.success("Zduplikowano zadanie! Znajdziesz je na zakładce Kolejka ze statusem Draft.")
            else:
                st.error("Błąd podczas duplikacji.")

    # TAB 2: Renderowanie podglądu HTML
    with tab2:
        st.subheader("Wizualny podgląd HTML")
        st.warning("Uwaga: To co tutaj widzisz, to tzw. 'Surowy Render'. Finalny wygląd tekstu po wrzuceniu na serwer (np. Magento/WordPress) zależy w 100% od zewnętrznych arkuszy CSS użytych w danym sklepie. Zablokowano wykonywanie zewnętrznych skryptów.")
        
        # Ochrona przed ewentualnym niebezpiecznym JS wygenerowanym przez AI (Zgodnie z wymaganiem usera)
        safe_html = (job.get("final_html") or "Brak głównej treści HTML").replace("<script", "&lt;script").replace("</script>", "&lt;/script&gt;")
        safe_faq = (job.get("faq_html") or "").replace("<script", "&lt;script").replace("</script>", "&lt;/script&gt;")
        
        # Meta wizualizacja
        st.markdown(f"<h2>{job.get('meta_title') or 'Brak Meta Title'}</h2>", unsafe_allow_html=True)
        st.markdown(f"<i>{job.get('meta_description') or 'Brak Meta Description'}</i><hr>", unsafe_allow_html=True)
        
        # Content
        st.markdown(safe_html, unsafe_allow_html=True)
        
        if safe_faq:
            st.markdown("---")
            st.markdown("### FAQ")
            st.markdown(safe_faq, unsafe_allow_html=True)
            
    # TAB 3: Oceny Atrakcyjności
    with tab3:
        st.subheader("Ocena Atrakcyjności Tekstu")
        
        attr_score = job.get("attractiveness_score")
        if attr_score is not None:
            st.metric("Ogólna ocena AI (Skuteczność / Atrakcyjność)", f"{attr_score}/10")
        else:
            st.info("Brak oceny atrakcyjności (zadanie wygenerowane w trybie SEO-only lub z pominięciem audytu).")
            
        attr_report = job.get("attractiveness_report_json")
        if attr_report:
            rules_qa = attr_report.get("rules_qa", {})
            st.markdown("### Reguły Marketingowe")
            
            has_cta = rules_qa.get("has_cta")
            st.metric("Wykryte Call To Action", "TAK" if has_cta else "NIE")
            
            generic_found = rules_qa.get("generic_phrases_found", [])
            if generic_found:
                st.warning(f"⚠️ Wykryto puste ogólniki (znaleziska z czarnej listy): {', '.join(generic_found)}")
            else:
                st.success("Wspaniale! Nie wykryto pustych ogólników w stylu AI.")
                
            forbidden = rules_qa.get("forbidden_phrases_found", [])
            if forbidden:
                st.error(f"🚨 Wykryto ZAKAZANE frazy: {', '.join(forbidden)}")
                
            required = rules_qa.get("required_phrases_missing", [])
            if required:
                st.warning(f"Brakujące wymagane frazy: {', '.join(required)}")
                
            ai_report = attr_report.get("ai_report")
            if ai_report:
                with st.expander("📝 Pełny audyt Atrakcyjności (AI JSON)"):
                    st.json(ai_report)

    # TAB 4: Szczegółowe metadane (QA, Logi per krok)
    with tab4:
        st.subheader("Parametry początkowe zlecenia")
        c1, c2 = st.columns(2)
        c1.write(f"**Data zlecenia:** `{job.get('created_at')}`")
        c1.write(f"**Główne słowo (Pillar):** `{job.get('main_keyword')}`")
        c1.write(f"**Poboczne słowa:** `{job.get('secondary_keywords') or 'Brak'}`")
        
        c2.write(f"**URL:** `{job.get('url') or 'Brak'}`")
        c2.write(f"**Wymagana Długość:** `{job.get('target_length') or 'Dowolna'}`")
        c2.write(f"**Dodatkowe wytyczne Custom:** `{job.get('additional_notes') or 'Brak'}`")
        
        # Raport z walidacji modelu
        if job.get("seo_report_json"):
            st.markdown("### 📊 Zautomatyzowane QA (Regułowe SEO)")
            
            qa = job["seo_report_json"].get("rules_qa", {})
            ai_qa = job["seo_report_json"].get("ai_report")
            
            if qa.get("is_empty"):
                st.warning("⚠️ Finalny kod HTML jest pusty! (Zadanie nie wygenerowało głównej treści).")
            else:
                if qa.get("is_markdown"):
                    st.warning("⚠️ Ostrzeżenie: Wykryto znaczniki Markdown (`#`, `**`). Model wypluł inny format niż kod HTML.")
                    
                rc1, rc2, rc3 = st.columns(3)
                
                # Znaków
                l_diff = qa.get('length_diff', 0)
                diff_str = f"+{l_diff}" if l_diff > 0 else f"{l_diff}"
                if l_diff == 0: diff_str = ""
                if qa.get('target_length') == 0: diff_str = "(Bez limitu)"
                rc1.metric("Długość (znaki ze spacjami)", f"{qa.get('char_count')}", diff_str)
                
                # Main keyword
                rc2.metric("Pojawienia głównej frazy", f"{qa.get('main_keyword_count')}")
                
                # H1 i H2
                h1_str = "TAK" if qa.get('has_h1') else "NIE"
                rc3.metric("Nagłówek H1", h1_str, f"{qa.get('h2_count')}x Nagłówki H2")
                
                st.write("**Wykorzystane frazy poboczne:**", ", ".join(qa.get("secondary_keywords_used", [])) or "Brak")
                if qa.get("secondary_keywords_missing"):
                    st.warning(f"**Niewykorzystane frazy poboczne:** {', '.join(qa.get('secondary_keywords_missing'))}")
                    
                # Zakazane tagi (które zostały wyczyszczone automatycznie)
                if qa.get("contains_forbidden_tags") or qa.get("contains_forbidden_attrs"):
                    st.error(f"Zanotowano interwencję Czyściciela HTML. Model zwrócił tagi: {qa.get('forbidden_tags_list')} oraz atrybuty: {qa.get('forbidden_attrs_list')}. Elementy te zostały automatycznie wyrzucone w procesie post-QA.")
                else:
                    st.success("Wygenerowany HTML był w 100% poprawny strukturalnie.")
            
            if ai_qa:
                with st.expander("📝 Raport kontroli jakości od sztucznej inteligencji (seo_qa step)"):
                    st.json(ai_qa)
            
        st.divider()
        st.subheader("Historia Kroków AI (Dziennik operacyjny)")
        steps = get_job_steps(selected_job_id)
        
        if not steps:
            st.info("Brak wykonanych kroków AI przypisanych do tego zlecenia.")
        else:
            total_in = sum(s.get("input_tokens") or 0 for s in steps)
            total_out = sum(s.get("output_tokens") or 0 for s in steps)
            st.write(f"**Całkowite zużycie LLM Tokenów dla zadania:** Input = `{total_in}`, Output = `{total_out}`")
            
            # Expandery pozwijane domyślnie
            for s in steps:
                color = "🟢" if s["status"] == "completed" else ("🔴" if s["status"] == "failed" else ("🟡" if s["status"] == "skipped" else "⚪"))
                with st.expander(f"{color} Krok {s['step_order']}: {s['step_name']} | Dostawca: {s['provider']} ({s['model']})"):
                    st.write(f"**Status wykonania:** `{s['status'].upper()}`")
                    
                    if s.get("input_tokens") or s.get("output_tokens"):
                        st.caption(f"Przepustowość dla kroku - Input (Kontekst): `{s['input_tokens']}` | Output (Wynik): `{s['output_tokens']}`")
                    
                    if s.get("error_message"):
                        st.error(f"Komunikat błędu silnika AI: {s['error_message']}")
                        
                    t_p, t_o = st.tabs(["📝 Instrukcje wejściowe (Użyty Prompt)", "🤖 Odpowiedź AI (Output)"])
                    with t_p:
                        st.markdown("**System Prompt (Rola AI):**")
                        st.code(s.get("system_prompt_used") or "Brak")
                        st.markdown("**User Prompt (Konkretne zlecenie podmienione):**")
                        st.code(s.get("user_prompt_used") or "Brak")
                    with t_o:
                        st.text_area("Czysty Tekst z API", value=s.get("output_text") or "", height=300, key=f"out_txt_{s['id']}", disabled=True)
                        if s.get("output_json"):
                            st.markdown("**Sparowany JSON przez aplikację:**")
                            st.json(s["output_json"])
