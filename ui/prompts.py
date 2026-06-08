import streamlit as st
from services.prompt_service import (
    get_campaign_prompt_sets, get_campaign_prompt_steps, get_default_prompt_sets,
    copy_default_to_campaign, update_campaign_prompt_step, restore_campaign_prompt_set,
    update_campaign_prompt_set
)
from utils.constants import PROVIDERS, MODELS_BY_PROVIDER
from db.supabase_client import get_supabase_client

# Opisy etapów dla użytkownika
STEP_DESCRIPTIONS = {
    "audience_insight": "Analizuje grupę docelową i definiuje personę na potrzeby kampanii.",
    "persuasion_strategy": "Wybiera frameworki perswazyjne (AIDA, PAS, FAB...) dopasowane do produktu.",
    "seo_outline": "Tworzy szkielet nagłówkowy (H1, H2) zoptymalizowany pod frazy kluczowe.",
    "seo_section_writer": "Pisze każdą sekcję tekstu osobno (pętla po nagłówkach H2), zapewniając spójność.",
    "main_content": "Generuje główny blok treści HTML.",
    "meta_title": "Tworzy zoptymalizowany meta title (maks. 60 znaków) z główną frazą.",
    "meta_description": "Tworzy atrakcyjny meta description (maks. 160 znaków) zachęcający do kliknięcia.",
    "faq": "Generuje sekcję FAQ z pytaniami i odpowiedziami wspierającymi SEO.",
    "html_cleanup": "Czyści i standaryzuje kod HTML — usuwa niedozwolone tagi i atrybuty.",
    "seo_qa": "Przeprowadza automatyczne SEO QA: sprawdza frazy, długość, nagłówki i strukturę.",
    "attractiveness_qa": "Ocenia atrakcyjność i marketingową skuteczność tekstu (skala 1–10 + raport).",
    "content_rewriter": "Przepisuje istniejący tekst zachowując SEO, ale poprawiając jakość i styl.",
    "brand_voice": "Dostosowuje ton i styl tekstu do archetypu i głosu marki zdefiniowanego w strategii.",
}

def render():
    st.title("📝 Prompty Kampanii")
    st.caption("Tutaj edytujesz instrukcje dla AI używane w tej kampanii. Zmiany nie modyfikują promptów domyślnych.")

    # Panel boczny z listą zmiennych (pomocny przy pisaniu promptów)
    with st.sidebar:
        st.subheader("📌 Dostępne zmienne w promptach")
        st.caption("Wstaw do pól System/User Prompt. Zostaną podmienione danymi zadania przy uruchomieniu.")
        with st.expander("Dane zadania", expanded=True):
            st.code(
                "{{main_keyword}}\n{{secondary_keywords}}\n{{language}}\n{{locale}}\n{{content_type}}\n"
                "{{target_length}}\n{{url}}\n{{current_content}}\n{{additional_notes}}",
                language=None
            )
        with st.expander("Strategia kampanii"):
            st.code(
                "{{target_audience}}\n{{persona}}\n{{consumer_insight}}\n{{brand_tone}}\n"
                "{{content_goal}}\n{{call_to_action}}\n{{required_phrases}}\n{{forbidden_phrases}}",
                language=None
            )
        with st.expander("Przepływ między etapami"):
            st.code(
                "{{previous_steps.NAZWA_KROKU}}\n(np. {{previous_steps.seo_outline}})\n\n"
                "{{headings}}   ← lista H2 do pętli\n{{heading}}    ← bieżący H2 w pętli\n"
                "{{already_written_part}}  ← dotychczasowy tekst\n{{current_step_output}}",
                language=None
            )

    active_camp_id = st.session_state.get("active_campaign_id")
    if not active_camp_id:
        st.warning("⚠️ Nie wybrano aktywnej kampanii. Wybierz kampanię z menu po lewej stronie, a następnie wróć tutaj.", icon="⚠️")
        return

    # ------------------------------------------------------------------
    # KOPIOWANIE DOMYŚLNEGO ZESTAWU
    # ------------------------------------------------------------------
    with st.expander("➕ Skopiuj nowy zestaw promptów z biblioteki systemowej"):
        st.write("Skopiuj domyślny zestaw etapów do tej kampanii. Możesz mieć kilka zestawów (np. jeden dla blogów, jeden dla kategorii).")
        default_sets = get_default_prompt_sets()
        if not default_sets:
            st.error("❌ Brak domyślnych zestawów w systemie. Wejdź do **Ustawień** i kliknij 'Zainicjuj domyślne prompty (Seed)'.")
        else:
            if st.button("📋 Skopiuj WSZYSTKIE domyślne zestawy do tej kampanii", type="primary"):
                with st.spinner("Klonowanie zestawów..."):
                    success_count = 0
                    for d in default_sets:
                        if copy_default_to_campaign(active_camp_id, d["id"]):
                            success_count += 1
                    if success_count > 0:
                        st.success(f"✅ Skopiowano {success_count} zestawów do kampanii.")
                        st.rerun()

    st.divider()

    # ------------------------------------------------------------------
    # WYBÓR ZESTAWU DO EDYCJI
    # ------------------------------------------------------------------
    camp_sets = get_campaign_prompt_sets(active_camp_id)
    if not camp_sets:
        st.info("Ta kampania nie ma jeszcze promptów. Skopiuj domyślny zestaw promptów, a potem dostosuj go do kampanii.")
        return

    st.subheader("Edycja Zestawu Promptów")
    camp_set_options = {s["id"]: s["name"] for s in camp_sets}
    selected_camp_set_id = st.selectbox(
        "Wybierz zestaw do edycji:",
        list(camp_set_options.keys()),
        format_func=lambda x: camp_set_options[x]
    )

    selected_set_data = next(s for s in camp_sets if s["id"] == selected_camp_set_id)

    col_name, col_meta, col_restore = st.columns([3, 2, 2])
    with col_name:
        new_set_name = st.text_input("Zmień nazwę zestawu", value=selected_set_data["name"], label_visibility="collapsed")
        if new_set_name != selected_set_data["name"] and new_set_name.strip():
            update_campaign_prompt_set(selected_camp_set_id, {"name": new_set_name})
            st.rerun()
    with col_meta:
        st.caption(f"Typ: **{selected_set_data['content_type']}** | Język: **{selected_set_data['language']}**")
    with col_restore:
        if st.button("🔄 Przywróć domyślne", type="secondary", help="Nadpisze wszystkie Twoje zmiany w tym zestawie fabryczną wersją."):
            st.session_state[f"confirm_restore_{selected_camp_set_id}"] = True

    if st.session_state.get(f"confirm_restore_{selected_camp_set_id}"):
        st.warning("⚠️ Czy na pewno chcesz przywrócić domyślny zestaw? **Wszystkie zmiany zostaną utracone** i nie będzie możliwości cofnięcia.")
        rc1, rc2 = st.columns([1, 6])
        if rc1.button("✅ Tak, przywróć", type="primary"):
            if restore_campaign_prompt_set(selected_camp_set_id):
                st.success("Przywrócono domyślny zestaw!")
            st.session_state[f"confirm_restore_{selected_camp_set_id}"] = False
            st.rerun()
        if rc2.button("❌ Anuluj"):
            st.session_state[f"confirm_restore_{selected_camp_set_id}"] = False
            st.rerun()

    st.markdown("---")

    # ------------------------------------------------------------------
    # LISTA ETAPÓW PODZIELONA NA GRUPY
    # ------------------------------------------------------------------
    steps = get_campaign_prompt_steps(selected_camp_set_id)
    if not steps:
        st.error("❌ Problem techniczny: brak kroków przypisanych do tego zestawu. Spróbuj przywrócić domyślne lub skontaktuj się z administratorem.")
        return

    GROUP_COLORS = {
        "seo": "🔵",
        "attractiveness": "🟣",
        "technical": "🟠"
    }
    GROUP_LABELS = {
        "seo": "SEO",
        "attractiveness": "Atrakcyjność",
        "technical": "Techniczne"
    }

    for step in steps:
        sg = step.get("stage_group", "seo")

        group_icon = GROUP_COLORS.get(sg, "⚪")
        group_label = GROUP_LABELS.get(sg, sg.upper())
        status_icon = "✅" if step["is_active"] else "⏸️ WYŁĄCZONY"

        expander_title = f"{group_icon} [{group_label}] Krok {step['step_order']}: **{step['step_name']}** — {status_icon}"

        with st.expander(expander_title, expanded=False):
            # Opis etapu dla użytkownika
            step_desc = STEP_DESCRIPTIONS.get(step.get("step_key", ""), "")
            if step_desc:
                st.caption(f"ℹ️ *{step_desc}*")

            # Przełącznik włącz/wyłącz etap
            is_active = st.toggle(
                f"Etap aktywny",
                value=step["is_active"],
                key=f"active_{step['id']}",
                help="Wyłączony etap zostanie całkowicie pominięty podczas generowania."
            )
            if is_active != step["is_active"]:
                update_campaign_prompt_step(step["id"], {"is_active": is_active})
                st.rerun()

            if not step["is_active"]:
                st.warning("⚠️ Ten etap jest wyłączony. Jeśli kolejne kroki powołują się na jego wynik, mogą zgłosić błąd lub wygenerować pusty output.")

            st.divider()

            # Formularz z ustawieniami
            with st.form(f"form_step_{step['id']}", border=False):
                col_p, col_m, col_t, col_tk = st.columns(4)

                prov_list = ["(Dziedzicz z zadania)"] + list(MODELS_BY_PROVIDER.keys())
                curr_prov = step.get("provider")
                prov_index = prov_list.index(curr_prov) if curr_prov in prov_list else 0
                
                selected_prov_ui = col_p.selectbox(
                    "Dostawca AI",
                    prov_list,
                    index=prov_index,
                    key=f"prov_{step['id']}"
                )
                provider = None if selected_prov_ui == "(Dziedzicz z zadania)" else selected_prov_ui

                if selected_prov_ui == "(Dziedzicz z zadania)":
                    flat_models = sorted(list(set([m for mods in MODELS_BY_PROVIDER.values() for m in mods])))
                else:
                    flat_models = MODELS_BY_PROVIDER.get(selected_prov_ui, [])
                
                mod_list = ["(Dziedzicz z zadania)"] + flat_models
                curr_model = step.get("model")
                mod_index = mod_list.index(curr_model) if curr_model in mod_list else 0
                
                selected_mod_ui = col_m.selectbox(
                    "Model",
                    mod_list,
                    index=mod_index,
                    key=f"mod_{step['id']}"
                )
                model = None if selected_mod_ui == "(Dziedzicz z zadania)" else selected_mod_ui

                temp = col_t.slider("Temperatura", 0.0, 2.0, float(step["temperature"] or 0.7), 0.1,
                                    help="Wyższa = bardziej kreatywna odpowiedź. Niższa = bardziej przewidywalna.")
                max_tok = col_tk.number_input("Max Tokens", 100, 16000, int(step["max_tokens"] or 4000), 100,
                                              help="Maksymalna długość odpowiedzi AI. 4000 tokenów ≈ ~3000 słów.")

                # Prompty w expanderach, żeby nie zaśmiecać ekranu
                with st.expander("📋 System Prompt (Rola i zasady działania AI)", expanded=False):
                    st.caption("Instrukcje operacyjne dla modelu — rola, zasady, zakazy. Zazwyczaj nie trzeba tu wchodzić.")
                    sys_prompt = st.text_area(
                        "System Prompt",
                        value=step.get("system_prompt", ""),
                        height=300,
                        label_visibility="collapsed"
                    )
                with st.expander("✍️ User Prompt (Treść polecenia z danymi zadania)", expanded=True):
                    st.caption("Tu wpisz konkretne instrukcje i wstaw zmienne w tagach XML-like, np. `<fraza_główna>{{main_keyword}}</fraza_główna>`.")
                    usr_prompt = st.text_area(
                        "User Prompt",
                        value=step.get("user_prompt", ""),
                        height=300,
                        label_visibility="collapsed"
                    )

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
                        st.success("✅ Zapisano! Zmiany wejdą w życie przy następnym uruchomieniu zadania.")
                        st.rerun()
                    else:
                        st.error("❌ Nie udało się zapisać. Sprawdź połączenie z bazą w zakładce Ustawienia.")
