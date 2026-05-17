import streamlit as st
from services.prompt_service import (
    get_campaign_prompt_sets, get_campaign_prompt_steps, get_default_prompt_sets,
    copy_default_to_campaign, update_campaign_prompt_step, restore_campaign_prompt_set,
    update_campaign_prompt_set
)
from utils.constants import PROVIDERS, MODELS_BY_PROVIDER

def render():
    st.title("Prompty Robocze Kampanii")
    
    # Wyświetlenie panelu bocznego z podpowiedzią zmiennych (można schować w sidebar, by był czytelny podczas edycji)
    with st.sidebar:
        st.subheader("Dostępne zmienne")
        st.info("Zmienne parsowane podczas uruchamiania generowania zadania z tagów {{tag}}.")
        st.markdown("""
        * `{{content_type}}`
        * `{{language}}`
        * `{{locale}}`
        * `{{main_keyword}}`
        * `{{secondary_keywords}}`
        * `{{target_length}}`
        * `{{current_content}}`
        * `{{additional_notes}}`
        * `{{url}}`
        * `{{is_existing_url}}`
        * `{{previous_steps.NAZWA_KROKU}}` (np. `{{previous_steps.outline}}`)
        """)
        
    active_camp_id = st.session_state.get("active_campaign_id")
    if not active_camp_id:
        st.warning("Najpierw musisz aktywować (wybrać) kampanię w widoku 'Kampanie'.", icon="⚠️")
        return
        
    # Akcja na górze: pobranie i tworzenie
    st.write("Każda kampania posiada swoje osobne klony domyślnych promptów. Zmiany nie wpływają na fabryczną konfigurację, ani na inne kampanie.")
    
    # Kontener do operacji dodawania nowego zestawu
    with st.expander("➕ Skopiuj dodatkowy domyślny zestaw do tej kampanii"):
        default_sets = get_default_prompt_sets()
        if not default_sets:
            st.error("Brak domyślnych promptów w systemie. Udaj się do 'Ustawienia' i wykonaj inicjalizację promptów (Seed).")
        else:
            def_options = {d["id"]: f"{d['name']} ({d['content_type']})" for d in default_sets}
            selected_def_id = st.selectbox("Wybierz zestaw źródłowy z biblioteki", options=list(def_options.keys()), format_func=lambda x: def_options[x])
            if st.button("Skopiuj do kampanii", type="primary"):
                with st.spinner("Kopiowanie 10 etapów..."):
                    if copy_default_to_campaign(active_camp_id, selected_def_id):
                        st.success("Sukces!")
                        st.rerun()

    st.divider()

    camp_sets = get_campaign_prompt_sets(active_camp_id)
    if not camp_sets:
        st.info("Kampania nie posiada jeszcze własnych promptów roboczych. Skorzystaj z panelu powyżej, aby je zaciągnąć.", icon="ℹ️")
        return
        
    # Wybór zestawu do edycji
    st.subheader("Edycja Zestawów")
    camp_set_options = {s["id"]: s["name"] for s in camp_sets}
    selected_camp_set_id = st.selectbox("Wybierz roboczy zestaw promptów do edycji:", list(camp_set_options.keys()), format_func=lambda x: camp_set_options[x])
    
    # Dane o zestawie
    selected_set_data = next(s for s in camp_sets if s["id"] == selected_camp_set_id)
    
    col_name, col_meta = st.columns([3, 2])
    with col_name:
        new_set_name = st.text_input("Zmień nazwę dla tego zestawu", value=selected_set_data["name"])
        if new_set_name != selected_set_data["name"]:
            update_campaign_prompt_set(selected_camp_set_id, {"name": new_set_name})
            st.rerun()
            
    with col_meta:
        st.write("")
        st.write("")
        st.caption(f"Typ treści: **{selected_set_data['content_type']}** | Język: **{selected_set_data['language']}**")
        
    # Funkcja ratunkowa
    if st.button("⚠️ Przywróć z domyślnych (Wyczyść zmiany)", type="secondary"):
        st.session_state[f"confirm_restore_{selected_camp_set_id}"] = True
        
    if st.session_state.get(f"confirm_restore_{selected_camp_set_id}"):
        st.warning("🚨 Czy NA PEWNO chcesz nadpisać całą listę etapów w tym zestawie ich domyślną, fabryczną wersją? Odwrócenie tej operacji nie będzie możliwe.")
        col1, col2 = st.columns([1, 10])
        if col1.button("Tak, przywróć", type="primary"):
            if restore_campaign_prompt_set(selected_camp_set_id):
                st.success("Przywrócono czysty zestaw!")
            st.session_state[f"confirm_restore_{selected_camp_set_id}"] = False
            st.rerun()
        if col2.button("Anuluj operację"):
            st.session_state[f"confirm_restore_{selected_camp_set_id}"] = False
            st.rerun()
            
    st.markdown("---")
    st.subheader("Lista Etapów (Kroków Generowania)")
    
    steps = get_campaign_prompt_steps(selected_camp_set_id)
    if not steps:
        st.error("Wystąpił problem techniczny, brak kroków przypisanych do tego zestawu.")
        return
        
    # Pętla przez kroki z użyciem Expandera
    for step in steps:
        header_icon = "🟢" if step['is_active'] else "⚫ (WYŁĄCZONY)"
        expander_title = f"{header_icon} Krok {step['step_order']}: {step['step_name']} | {step['provider']} ({step['model']})"
        
        with st.expander(expander_title):
            # Przełącznik aktywności on_change (bez st.form dla bezpieczeństwa natychmiastowego zapisu)
            is_active = st.checkbox(f"Włącz etap ({step['step_key']})", value=step["is_active"], key=f"active_{step['id']}")
            if is_active != step["is_active"]:
                update_campaign_prompt_step(step["id"], {"is_active": is_active})
                st.rerun()
                
            if not step["is_active"]:
                st.warning("⚠️ Ten etap zostanie całkowicie pominięty podczas generowania, co może spowodować błędy w kolejnych krokach powołujących się na zmienną z tego kroku.")
                
            # Formularz izolujący przycisk zapisywania, by ułatwić modyfikację
            with st.form(f"form_step_{step['id']}", border=False):
                col_p, col_m, col_t, col_tk = st.columns(4)
                
                # Provider logic
                prov_list = list(MODELS_BY_PROVIDER.keys())
                provider = col_p.selectbox("Provider AI", prov_list, index=prov_list.index(step["provider"]) if step.get("provider") in prov_list else 0)
                
                # Flattening models dla fallbacka
                flat_models = list(set([m for mods in MODELS_BY_PROVIDER.values() for m in mods]))
                # Choć teoretycznie pokazujemy wszystkie aby nie wymuszać podwójnego reruna, Streamlit 1.32 radzi z tym sobie bezbłędnie
                model = col_m.selectbox("Model", flat_models, index=flat_models.index(step["model"]) if step.get("model") in flat_models else 0)
                
                temp = col_t.slider("Temperatura", 0.0, 2.0, float(step["temperature"] or 0.7), 0.1)
                max_tok = col_tk.number_input("Max Tokens", 100, 16000, int(step["max_tokens"] or 4000), 100)
                
                sys_prompt = st.text_area("System Prompt (kontekst roli)", value=step.get("system_prompt", ""), height=100)
                usr_prompt = st.text_area("User Prompt (polecenie per zadanie)", value=step.get("user_prompt", ""), height=250)
                
                if st.form_submit_button("💾 Zapisz ustawienia etapu", type="primary"):
                    update_data = {
                        "provider": provider,
                        "model": model,
                        "temperature": temp,
                        "max_tokens": max_tok,
                        "system_prompt": sys_prompt.strip(),
                        "user_prompt": usr_prompt.strip()
                    }
                    if update_campaign_prompt_step(step["id"], update_data):
                        st.success("Zapisano! Widok zostanie zaktualizowany...")
                        # Obejście dla płynności
                        st.rerun()
