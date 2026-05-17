import streamlit as st
from services.job_repository import create_content_job, create_prompt_snapshots_for_job
from services.prompt_service import get_campaign_prompt_sets, get_campaign_prompt_steps
from services.campaign_service import get_campaign_by_id
from utils.constants import CONTENT_TYPES, LOCALES, PROVIDERS, MODELS_BY_PROVIDER

def render():
    st.title("Nowa treść")
    st.write("Dodaj pojedyncze zadanie do wygenerowania treści.")
    
    # 1. Sprawdzenie wymagań wejściowych
    active_camp_id = st.session_state.get("active_campaign_id")
    if not active_camp_id:
        st.warning("Najpierw musisz aktywować (wybrać) kampanię w widoku 'Kampanie'.", icon="⚠️")
        return
        
    campaign = get_campaign_by_id(active_camp_id)
    if not campaign:
        st.error("Błąd krytyczny: Wybrana kampania nie istnieje w bazie (mogła zostać usunięta).")
        return
        
    st.markdown(f"Dodajesz zadanie do kampanii: **`{campaign['name']}`**")
    
    prompt_sets = get_campaign_prompt_sets(active_camp_id)
    if not prompt_sets:
        st.error("🚨 Ta kampania nie posiada żadnych zestawów promptów roboczych. Zanim utworzysz zadanie, przejdź do zakładki 'Prompty' i skopiuj bibliotekę domyślną.")
        return
        
    # 2. Wybór szablonu (Poza głównym formularzem, bo chcemy dynamicznie reagować na zmianę ładując inne kroki)
    st.subheader("Źródło konfiguracji AI")
    set_options = {s["id"]: s["name"] for s in prompt_sets}
    selected_set_id = st.selectbox("Wybierz zestaw promptów bazowych:", list(set_options.keys()), format_func=lambda x: set_options[x])
    selected_set = next(s for s in prompt_sets if s["id"] == selected_set_id)
    
    # Natychmiastowe dociągnięcie kroków dla wybranego setu
    steps = get_campaign_prompt_steps(selected_set_id)
    
    st.divider()
    
    # 3. Główny Formularz Zadania
    st.subheader("Konfiguracja Zadania")
    
    with st.form("new_job_form", border=False):
        # Sekcja: Dane podstawowe
        st.markdown("#### 1. Dane podstawowe")
        c1, c2 = st.columns(2)
        
        # Próba mapowania na wartości domyślne setu
        ct_idx = CONTENT_TYPES.index(selected_set["content_type"]) if selected_set.get("content_type") in CONTENT_TYPES else 0
        content_type = c1.selectbox("Typ contentu *", CONTENT_TYPES, index=ct_idx)
        
        locales_list = list(LOCALES.keys())
        # Wykrywanie języka na bazie locale, domyślnie 0 (pl-PL)
        loc_idx = 0
        for i, loc in enumerate(locales_list):
            if LOCALES[loc] == selected_set.get("language"):
                loc_idx = i
                break
        locale = c2.selectbox("Język / Region docelowy *", locales_list, index=loc_idx)
        
        c3, c4 = st.columns([3, 1])
        url = c3.text_input("Adres URL (opcjonalnie)")
        is_existing = c4.checkbox("Aktualizuj treść istniejącego URL", value=False)
        
        # Sekcja: SEO
        st.markdown("#### 2. SEO i Frazy Kluczowe")
        main_keyword = st.text_input("Główne słowo kluczowe *", placeholder="Np. buty sportowe damskie", help="Najważniejsza fraza SEO, wokół której ma powstać treść.")
        secondary_keywords = st.text_area("Poboczne słowa kluczowe (po przecinku)", placeholder="buty do biegania, tanie sneakersy, nike, adidas", help="Frazy pomocnicze. Nie będą upychane na siłę — model użyje ich naturalnie.")
        target_length = st.number_input("Docelowa długość (znaki bez spacji, opcjonalnie)", min_value=0, value=0, step=500, help="Docelowa długość tekstu w znakach ze spacjami. Model może nie trafić idealnie, ale aplikacja pokaże różnicę.")
        
        # Sekcja: Istniejąca treść
        st.markdown("#### 3. Treść i wytyczne (Opcjonalnie)")
        current_content = st.text_area("Istniejąca treść (do zadania typu 'Rewrite' lub 'Optymalizacja')", height=150, help="Wklej obecną treść strony, jeśli chcesz ją poprawić lub rozbudować.")
        additional_notes = st.text_area("Dodatkowe wytyczne dla AI (będą wstrzyknięte do analizy)", placeholder="Napisz luzem. Zwróć uwagę na ton marki...", help="Zostaną dodane jako dodatkowy kontekst.")
        
        # Sekcja: Tryb i Strategia
        st.markdown("#### 4. Atrakcyjność i Skuteczność Tekstu (Opcjonalnie)")
        gen_mode_opts = {
            "seo_and_attractiveness": "SEO + Atrakcyjność (Pełny Pipeline)",
            "seo_only": "Tylko SEO (Szybkie i Klasyczne)",
            "attractiveness_only": "Tylko Atrakcyjność (np. dla istniejących tekstów)",
            "quick_content": "Szybki tekst (Zoptymalizowany Pipeline)"
        }
        generation_mode = st.selectbox("Tryb generowania", list(gen_mode_opts.keys()), format_func=lambda x: gen_mode_opts[x])
        
        with st.expander("Nadpisz strategię kampanii dla tego konkretnego zadania"):
            content_goal = st.text_input("Cel tekstu", help="Np. edukacja, sprzedaż, przejście do kategorii, zapis na konsultację.")
            call_to_action = st.text_input("Call To Action (CTA)", help="Docelowe wezwanie do działania, np. sprawdź ofertę, skontaktuj się, pobierz poradnik.")
            target_audience_override = st.text_input("Grupa docelowa (Nadpisz)")
            persona_override = st.text_input("Persona (Nadpisz)")
            tone_override = st.text_input("Ton (Nadpisz)", help="Np. ekspercki, prosty, empatyczny, premium, techniczny.")
        
        # Sekcja: Globalne ustawienia nadpisujące z kampanii
        st.markdown("#### 5. Parametry wykonawcze")
        p1, p2, p3 = st.columns([2, 2, 1])
        
        # Domyślne mapowanie z samej kampanii jako 'podpowiedź', choć per krok mogą być inne
        cmp_prov_idx = PROVIDERS.index(campaign.get("default_provider")) if campaign.get("default_provider") in PROVIDERS else 0
        provider = p1.selectbox("Globalny Provider Awaryjny", PROVIDERS, index=cmp_prov_idx, help="Używany gdy krok z jakiegoś powodu nie zdefiniuje swojego")
        
        flat_models = list(set([m for mods in MODELS_BY_PROVIDER.values() for m in mods]))
        mod_idx = flat_models.index(campaign.get("default_model")) if campaign.get("default_model") in flat_models else 0
        model = p2.selectbox("Globalny Model Awaryjny", flat_models, index=mod_idx)
        
        if model and ("gpt-4" in model or "opus" in model):
            st.warning("⚠️ Wybrano bardzo drogi model. Upewnij się, że budżet kampanii na to pozwala.")
            
        priority = p3.number_input("Priorytet (Wyższy = szybszy start)", min_value=0, max_value=100, value=0)
        
        # Sekcja: Pipeline (Modyfikacja w locie)
        st.markdown("#### 6. Przegląd i selekcja etapów (Pipeline)")
        st.info("Poniżej znajduje się lista kroków dla tego zestawu. Checkboxy zostały dostosowane na podstawie wybranego Trybu Generowania.")
        
        for step in steps:
            sg = step.get("stage_group", "seo")
            default_active = step["is_active"]
            
            if generation_mode == "seo_only" and sg == "attractiveness":
                default_active = False
            elif generation_mode == "attractiveness_only" and sg == "seo":
                if step["step_key"] not in ["main_content", "html_cleanup"]:
                    default_active = False
            elif generation_mode == "quick_content":
                quick_keys = ["audience_insight", "persuasion_strategy", "main_content", "attractiveness_optimization", "html_cleanup", "seo_qa", "attractiveness_qa"]
                if step["step_key"] not in quick_keys:
                    default_active = False
            
            # Renderujemy standardowe checkboxy, Streamlit sczyta ich status w momencie kliknięcia w submit
            st.checkbox(
                f"[{step['step_order']}] {step['step_name']} ({sg.upper()})", 
                value=default_active, 
                key=f"step_toggle_{step['id']}"
            )
            
        st.divider()
        st.write("Wybierz jedną z akcji po sprawdzeniu konfiguracji:")
        b1, b2, _ = st.columns([2, 2, 6])
        submit_draft = b1.form_submit_button("📦 Zapisz jako Draft", type="secondary", use_container_width=True)
        submit_queue = b2.form_submit_button("▶️ Dodaj do kolejki", type="primary", use_container_width=True)
        
        # Logika obsługi formularza
        if submit_draft or submit_queue:
            if not main_keyword.strip():
                st.error("Główne słowo kluczowe jest wymagane!")
            elif target_length < 0:
                st.error("Docelowa długość musi być nieujemna.")
            elif target_length > 15000:
                st.error("Wymagasz zbyt długiego tekstu (ponad 15000 znaków). Modele AI zazwyczaj ucinają odpowiedź wokół 4000-8000 znaków. Jeśli chcesz dłuższy tekst, ustaw mniejsze sekcje lub zignoruj to pole.")
            elif current_content and len(current_content) > 30000:
                st.error("Wklejona obecna treść jest bardzo długa (powyżej 30k znaków). Może to spowodować przekroczenie limitu tokenów lub błędy timeoutów.")
            else:
                status = "queued" if submit_queue else "draft"
                
                # Budowanie DTO
                job_data = {
                    "campaign_id": active_camp_id,
                    "operator_name": st.session_state.get("current_operator", "N/A"),
                    "content_type": content_type,
                    "language": LOCALES[locale],
                    "locale": locale,
                    "url": url.strip() if url.strip() else None,
                    "is_existing_url": is_existing,
                    "main_keyword": main_keyword.strip(),
                    "secondary_keywords": secondary_keywords.strip() if secondary_keywords.strip() else None,
                    "target_length": target_length if target_length > 0 else None,
                    "current_content": current_content.strip() if current_content.strip() else None,
                    "additional_notes": additional_notes.strip() if additional_notes.strip() else None,
                    "provider": provider,
                    "model": model,
                    "status": status,
                    "priority": priority,
                    "generation_mode": generation_mode,
                    "content_goal": content_goal.strip() if content_goal.strip() else None,
                    "call_to_action": call_to_action.strip() if call_to_action.strip() else None,
                    "target_audience_override": target_audience_override.strip() if target_audience_override.strip() else None,
                    "persona_override": persona_override.strip() if persona_override.strip() else None,
                    "tone_override": tone_override.strip() if tone_override.strip() else None
                }
                
                job_id = create_content_job(job_data)
                
                if job_id:
                    # Wyciągnięcie informacji o checkboxach z `st.session_state` po kluczach
                    job_step_toggles = {}
                    for step in steps:
                        # Domyślnie bierzemy stan z bazy, ale jak klucz istnieje w st.session_state to nadpisujemy
                        chk_val = st.session_state.get(f"step_toggle_{step['id']}", step["is_active"])
                        job_step_toggles[step["id"]] = chk_val
                        
                    # Zrzut snapshotu
                    if create_prompt_snapshots_for_job(job_id, steps, job_step_toggles):
                        if status == "queued":
                            st.success("✅ Dodano zadanie do kolejki. Przejdź do 'Kolejka generowania', by uruchomić przetwarzanie.")
                        else:
                            st.success("✅ Zapisano szkielet zadania (Draft).")
                    else:
                        st.warning("Zadanie utworzone z problemami. Brak snapshotu promptów – usuń zadanie i ponów próbę.")
