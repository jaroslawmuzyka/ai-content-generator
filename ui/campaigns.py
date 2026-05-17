import streamlit as st
from services.campaign_service import get_campaigns, get_campaign_by_id, create_campaign, update_campaign, archive_campaign
from utils.constants import CONTENT_TYPES, LOCALES, PROVIDERS, MODELS_BY_PROVIDER

def render():
    st.title("📂 Kampanie Contentowe")
    st.write("Kampania to paczka treści lub projekt contentowy, np. wpisy blogowe na dany miesiąc albo opisy produktów dla wybranej kategorii.")
    
    # Stan widoku: list, create, edit
    view_mode = st.session_state.get("campaign_view_mode", "list")
    
    if view_mode == "list":
        show_list_view()
    elif view_mode == "create":
        show_create_view()
    elif view_mode == "edit":
        show_edit_view()

def set_view_mode(mode):
    """Zmienia bieżący widok w sekcji kampanii."""
    st.session_state["campaign_view_mode"] = mode
    st.rerun()

def show_list_view():
    col1, col2, col3 = st.columns([2, 2, 6])
    with col1:
        st.button("➕ Nowa kampania", on_click=lambda: set_view_mode("create"), type="primary", use_container_width=True)
    with col2:
        status_filter = st.selectbox("Filtruj po statusie", ["active", "archived", "all"], index=0, label_visibility="collapsed")
        
    st.divider()
    
    # Pobieranie z Supabase (przez serwis)
    campaigns = get_campaigns(status_filter)
    
    if not campaigns:
        st.info("Nie masz jeszcze kampanii. Utwórz pierwszą kampanię, żeby zacząć generować treści.", icon="ℹ️")
        return
        
    active_id = st.session_state.get("active_campaign_id")
    
    # Renderowanie listy jako rozbudowane wiersze
    for camp in campaigns:
        is_active = (camp["id"] == active_id)
        
        # Wyświetlanie jako card
        container = st.container(border=True)
        with container:
            # Nagłówek
            title_col, badge_col = st.columns([4, 1])
            with title_col:
                header_text = f"### {camp['name']}"
                if is_active:
                    header_text += " 🟢 *(Wybrana do edycji zadań)*"
                st.markdown(header_text)
            
            with badge_col:
                if camp['status'] == 'archived':
                    st.caption("📦 *Zarchiwizowana*")
                else:
                    st.caption("✨ *Aktywna*")

            # Informacje
            info_col, action_col1, action_col2 = st.columns([3, 1, 1])
            with info_col:
                st.write(
                    f"**Typ:** `{camp.get('default_content_type', '-')}` | "
                    f"**Język:** `{camp.get('default_locale', '-')}` | "
                    f"**AI:** `{camp.get('default_provider', '-')} ({camp.get('default_model', '-')})`"
                )
                if camp.get("description"):
                    st.caption(camp["description"])
                    
            # Przyciski akcji
            with action_col1:
                if st.button("Ustaw aktywną", key=f"sel_{camp['id']}", disabled=is_active, use_container_width=True):
                    st.session_state["active_campaign_id"] = camp["id"]
                    st.rerun()
                    
                if st.button("Edytuj", key=f"edit_{camp['id']}", use_container_width=True):
                    st.session_state["campaign_edit_id"] = camp["id"]
                    set_view_mode("edit")
                    
            with action_col2:
                if camp["status"] != "archived":
                    if st.button("Archiwizuj", key=f"arch_{camp['id']}", type="secondary", use_container_width=True):
                        archive_campaign(camp["id"])
                        if is_active:
                            st.session_state["active_campaign_id"] = None
                        st.rerun()

def show_create_view():
    st.subheader("Tworzenie nowej kampanii")
    st.info("Poniższe ustawienia to tylko domyślne podpowiedzi dla nowych zadań. Przy generowaniu każdego tekstu będziesz mógł je zmienić.")
    
    # Nie używamy st.form, aby selectboxy AI mogły się dynamicznie odświeżać
    name = st.text_input("Nazwa kampanii *", placeholder="Np. Blog Tech, Landingi Wiosna", help="Wybierz nazwę, która pozwoli Ci łatwo zidentyfikować tę paczkę tekstów w przyszłości.", key="new_camp_name")
    description = st.text_area("Krótki opis projektu (Opcjonalne)", placeholder="Opcjonalna notatka o założeniach tego projektu.", key="new_camp_desc")
    
    with st.expander("Ustawienia domyślne dla tej kampanii (Rozwiń)", expanded=False):
        c1, c2 = st.columns(2)
        content_type = c1.selectbox("Domyślny typ contentu", CONTENT_TYPES, key="new_camp_ct")
        locale = c2.selectbox("Domyślny język/locale", list(LOCALES.keys()), key="new_camp_loc")
        
        c3, c4 = st.columns(2)
        provider = c3.selectbox("Domyślny dostawca AI", PROVIDERS, key="new_camp_prov")
        model = c4.selectbox("Domyślny model AI", MODELS_BY_PROVIDER.get(provider, []), key="new_camp_mod")
    
    st.write("") # Odstęp
    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 4])
    
    if col_btn1.button("💾 Zapisz Kampanię", type="primary", use_container_width=True):
        if not name.strip():
            st.error("Nazwa kampanii jest wymagana!")
        else:
            with st.spinner("Zapisuję..."):
                data = {
                    "name": name.strip(),
                    "description": description.strip(),
                    "default_content_type": content_type,
                    "default_language": LOCALES[locale],
                    "default_locale": locale,
                    "default_provider": provider,
                    "default_model": model,
                    "status": "active",
                    "created_by": st.session_state.get("current_operator", "unknown")
                }
                new_camp = create_campaign(data)
                if new_camp:
                    st.success("✅ Kampania została utworzona.")
                    
                    # Automatyczne ustawienie kampanii jako aktywnej
                    st.session_state["active_campaign_id"] = new_camp["id"]
                    
                    st.markdown("### Co dalej?")
                    st.markdown("1. 🎯 Przejdź do **Strategia Treści** i opisz personę/markę, by teksty były lepsze (Opcjonalnie).")
                    st.markdown("2. 📝 Przejdź do **Prompty** i kliknij 'Skopiuj Systemowy', by maszyna dostała instrukcje (Wymagane!).")
                    st.markdown("3. ➕ Przejdź do **Nowe Zadanie** lub **Import XLSX** aby dodać słowa kluczowe do wygenerowania.")
                    
                    if st.button("Wróć do listy kampanii", type="secondary"):
                        set_view_mode("list")
                        st.rerun()
                    return # Stop renderowania reszty formularza
                    
    if col_btn2.button("Anuluj", use_container_width=True):
        set_view_mode("list")

def show_edit_view():
    st.subheader("Edycja kampanii")
    
    camp_id = st.session_state.get("campaign_edit_id")
    if not camp_id:
        st.error("Nie wybrano kampanii do edycji.")
        if st.button("Wróć do listy"):
            set_view_mode("list")
        return
        
    camp = get_campaign_by_id(camp_id)
    if not camp:
        st.error("Nie znaleziono kampanii. Mogła zostać usunięta z bazy.")
        if st.button("Wróć do listy"):
            set_view_mode("list")
        return
        
    name = st.text_input("Nazwa kampanii *", value=camp.get("name", ""), key="edit_camp_name")
    description = st.text_area("Opis projektu", value=camp.get("description", "") or "", key="edit_camp_desc")
    
    c1, c2 = st.columns(2)
    ct_idx = CONTENT_TYPES.index(camp.get("default_content_type")) if camp.get("default_content_type") in CONTENT_TYPES else 0
    content_type = c1.selectbox("Domyślny typ contentu", CONTENT_TYPES, index=ct_idx, key="edit_camp_ct")
    
    loc_keys = list(LOCALES.keys())
    loc_idx = loc_keys.index(camp.get("default_locale")) if camp.get("default_locale") in loc_keys else 0
    locale = c2.selectbox("Domyślny język/locale", loc_keys, index=loc_idx, key="edit_camp_loc")
    
    c3, c4 = st.columns(2)
    prov_idx = PROVIDERS.index(camp.get("default_provider")) if camp.get("default_provider") in PROVIDERS else 0
    provider = c3.selectbox("Domyślny provider AI", PROVIDERS, index=prov_idx, key="edit_camp_prov")
    
    models = MODELS_BY_PROVIDER.get(provider, [])
    # Bezpieczne poszukiwanie modelu (mógł zniknąć z konfiguracji)
    mod_idx = models.index(camp.get("default_model")) if camp.get("default_model") in models else 0
    model = c4.selectbox("Domyślny model AI", models, index=mod_idx, key="edit_camp_mod")
    
    st.write("") # Odstęp
    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 4])
    
    if col_btn1.button("💾 Zapisz zmiany", type="primary", use_container_width=True):
        if not name.strip():
            st.error("Nazwa kampanii jest wymagana!")
        else:
            with st.spinner("Zapisuję..."):
                data = {
                    "name": name.strip(),
                    "description": description.strip(),
                    "default_content_type": content_type,
                    "default_language": LOCALES[locale],
                    "default_locale": locale,
                    "default_provider": provider,
                    "default_model": model,
                }
                updated = update_campaign(camp_id, data)
                if updated:
                    st.success("Zapisano zmiany!")
                    set_view_mode("list")
                    
    if col_btn2.button("Anuluj", use_container_width=True):
        set_view_mode("list")
