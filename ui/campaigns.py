import streamlit as st
from services.campaign_service import get_campaigns, get_campaign_by_id, create_campaign, update_campaign, archive_campaign
from services.jina_service import fetch_jina_content
from utils.constants import CONTENT_TYPES, LOCALES, PROVIDERS, MODELS_BY_PROVIDER

def render():
    col_t1, col_t2 = st.columns([8, 2])
    with col_t1:
        st.title("📂 Kampanie Contentowe")
    with col_t2:
        st.write("") 
        st.button("➕ Nowa kampania", on_click=lambda: set_view_mode("create"), type="primary", use_container_width=True, key="top_new_camp_btn")
        
    st.write("Kampania to paczka treści lub projekt contentowy, np. wpisy blogowe na dany miesiąc albo opisy produktów dla wybranej kategorii.")
    
    # Synchronizacja wyboru z bocznego paska
    last_sidebar_active = st.session_state.get("campaign_last_sidebar_active")
    current_active = st.session_state.get("active_campaign_id")
    if current_active and current_active != last_sidebar_active:
        st.session_state["campaign_view_mode"] = "edit"
        st.session_state["campaign_edit_id"] = current_active
        st.session_state["campaign_last_sidebar_active"] = current_active
        
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
    col1, col2 = st.columns([2, 8])
    with col1:
        status_filter = st.selectbox("Filtruj po statusie", ["active", "archived", "all"], index=0)
        
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
        
    with st.expander("Integracja Jina AI (Web Scraping)", expanded=False):
        c_jeng, c_jret = st.columns(2)
        jina_engine = c_jeng.selectbox("Silnik (Engine)", ["cf-browser-rendering", "playwright", "default"], index=0, help="Silnik używany przez Jina.", key="new_camp_jeng")
        jina_retain_images = c_jret.selectbox("Retain Images", ["none", "all", "block"], index=0, help="Domyślnie 'none'.", key="new_camp_jret")
        
        st.markdown("---")
        
        def render_jina_test_btn_create(label, selector_val, key_suffix):
            st.markdown("<br>", unsafe_allow_html=True)
            with st.popover(f"🧪 Testuj", use_container_width=True):
                st.write(f"**Test selektora:** `{label}`")
                local_test_url = st.text_input("Adres URL do testu:", placeholder="https://sklep.pl/kategoria...", key=f"pop_url_cr_{key_suffix}")
                if st.button("Uruchom zapytanie", key=f"run_test_cr_{key_suffix}", type="primary"):
                    if not local_test_url or not selector_val:
                        st.warning("Podaj adres URL do testu oraz wpisz selektor.")
                    else:
                        with st.spinner(f"Odpytywanie Jina AI..."):
                            j_key = st.secrets.get("JINA_API_KEY") if hasattr(st, "secrets") else None
                            if not j_key:
                                st.error("Brak klucza JINA_API_KEY w secrets.toml!")
                            else:
                                out, err = fetch_jina_content(local_test_url.strip(), j_key, jina_engine, selector_val.strip(), None, jina_retain_images)
                                if out:
                                    st.success("✅ Sukces!")
                                    st.code(out, language="markdown")
                                else:
                                    st.error(f"❌ Pusty wynik lub błąd: {err}")

        st.markdown("##### Scrapowanie Kategorii")
        c_j1, c_btn1 = st.columns([4, 1])
        with c_j1:
            jina_category_target = st.text_input("Category Target Selector", placeholder=".brand-list-wrapper", key="new_camp_jct")
        with c_btn1:
            render_jina_test_btn_create("Category", jina_category_target, "ct")
        jina_category_remove = st.text_input("Category Remove Selector", placeholder=".refinement-content, .add-to-cart", key="new_camp_jcr")
        
        st.markdown("##### Scrapowanie Produktów")
        p_j1, p_btn1 = st.columns([4, 1])
        with p_j1:
            jina_product_target = st.text_input("Product Target Selector", placeholder='#description [itemprop="description"]', key="new_camp_jpt")
        with p_btn1:
            render_jina_test_btn_create("Product", jina_product_target, "pt")
        jina_product_remove = st.text_input("Product Remove Selector", placeholder=".related-products", key="new_camp_jpr")
        
        st.markdown("##### Okruszki (Breadcrumbs)")
        bf_1, btn_bf1 = st.columns([4, 1])
        with bf_1:
            jina_breadcrumbs_target = st.text_input("Breadcrumbs Target", placeholder=".breadcrumbs", key="new_camp_jbt")
        with btn_bf1:
            render_jina_test_btn_create("Breadcrumbs", jina_breadcrumbs_target, "bt")

        st.markdown("##### Filtry (Filters)")
        bf_2, btn_bf2 = st.columns([4, 1])
        with bf_2:
            jina_filters_target = st.text_input("Filters Target", placeholder=".filters-wrapper", key="new_camp_jft")
        with btn_bf2:
            render_jina_test_btn_create("Filters", jina_filters_target, "ft")
    
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
                    "jina_engine": jina_engine,
                    "jina_retain_images": jina_retain_images,
                    "jina_category_target": jina_category_target.strip() if jina_category_target else None,
                    "jina_category_remove": jina_category_remove.strip() if jina_category_remove else None,
                    "jina_product_target": jina_product_target.strip() if jina_product_target else None,
                    "jina_product_remove": jina_product_remove.strip() if jina_product_remove else None,
                    "jina_breadcrumbs_target": jina_breadcrumbs_target.strip() if jina_breadcrumbs_target else None,
                    "jina_filters_target": jina_filters_target.strip() if jina_filters_target else None,
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
    
    with st.expander("Integracja Jina AI (Web Scraping)", expanded=False):
        c_jeng, c_jret = st.columns(2)
        j_engs = ["cf-browser-rendering", "playwright", "default"]
        curr_eng = camp.get("jina_engine") or "cf-browser-rendering"
        j_idx = j_engs.index(curr_eng) if curr_eng in j_engs else 0
        jina_engine = c_jeng.selectbox("Silnik (Engine)", j_engs, index=j_idx, help="Silnik używany przez Jina.", key="edit_camp_jeng")
        
        j_rets = ["none", "all", "block"]
        curr_ret = camp.get("jina_retain_images") or "none"
        jr_idx = j_rets.index(curr_ret) if curr_ret in j_rets else 0
        jina_retain_images = c_jret.selectbox("Retain Images", j_rets, index=jr_idx, help="Domyślnie 'none'.", key="edit_camp_jret")
        
        st.markdown("---")
        
        def render_jina_test_btn_edit(label, selector_val, key_suffix):
            st.markdown("<br>", unsafe_allow_html=True)
            with st.popover(f"🧪 Testuj", use_container_width=True):
                st.write(f"**Test selektora:** `{label}`")
                local_test_url = st.text_input("Adres URL do testu:", placeholder="https://sklep.pl/kategoria...", key=f"pop_url_ed_{key_suffix}")
                if st.button("Uruchom zapytanie", key=f"run_test_ed_{key_suffix}", type="primary"):
                    if not local_test_url or not selector_val:
                        st.warning("Podaj adres URL do testu oraz wpisz selektor.")
                    else:
                        with st.spinner(f"Odpytywanie Jina AI..."):
                            j_key = st.secrets.get("JINA_API_KEY") if hasattr(st, "secrets") else None
                            if not j_key:
                                st.error("Brak klucza JINA_API_KEY w secrets.toml!")
                            else:
                                out, err = fetch_jina_content(local_test_url.strip(), j_key, jina_engine, selector_val.strip(), None, jina_retain_images)
                                if out:
                                    st.success("✅ Sukces!")
                                    st.code(out, language="markdown")
                                else:
                                    st.error(f"❌ Pusty wynik lub błąd: {err}")

        st.markdown("##### Scrapowanie Kategorii")
        c_j1, c_btn1 = st.columns([4, 1])
        with c_j1:
            jina_category_target = st.text_input("Category Target Selector", value=camp.get("jina_category_target") or "", placeholder=".brand-list-wrapper", key="edit_camp_jct")
        with c_btn1:
            render_jina_test_btn_edit("Category", jina_category_target, "ct")
        jina_category_remove = st.text_input("Category Remove Selector", value=camp.get("jina_category_remove") or "", placeholder=".refinement-content, .add-to-cart", key="edit_camp_jcr")
        
        st.markdown("##### Scrapowanie Produktów")
        p_j1, p_btn1 = st.columns([4, 1])
        with p_j1:
            jina_product_target = st.text_input("Product Target Selector", value=camp.get("jina_product_target") or "", placeholder='#description [itemprop="description"]', key="edit_camp_jpt")
        with p_btn1:
            render_jina_test_btn_edit("Product", jina_product_target, "pt")
        jina_product_remove = st.text_input("Product Remove Selector", value=camp.get("jina_product_remove") or "", placeholder=".related-products", key="edit_camp_jpr")
        
        st.markdown("##### Okruszki (Breadcrumbs)")
        bf_1, btn_bf1 = st.columns([4, 1])
        with bf_1:
            jina_breadcrumbs_target = st.text_input("Breadcrumbs Target Selector", value=camp.get("jina_breadcrumbs_target") or "", placeholder=".breadcrumbs", key="edit_camp_jbt")
        with btn_bf1:
            render_jina_test_btn_edit("Breadcrumbs", jina_breadcrumbs_target, "bt")

        st.markdown("##### Filtry (Filters)")
        bf_2, btn_bf2 = st.columns([4, 1])
        with bf_2:
            jina_filters_target = st.text_input("Filters Target Selector", value=camp.get("jina_filters_target") or "", placeholder=".filters-wrapper", key="edit_camp_jft")
        with btn_bf2:
            render_jina_test_btn_edit("Filters", jina_filters_target, "ft")
    
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
                    "jina_engine": jina_engine,
                    "jina_retain_images": jina_retain_images,
                    "jina_category_target": jina_category_target.strip() if jina_category_target else None,
                    "jina_category_remove": jina_category_remove.strip() if jina_category_remove else None,
                    "jina_product_target": jina_product_target.strip() if jina_product_target else None,
                    "jina_product_remove": jina_product_remove.strip() if jina_product_remove else None,
                    "jina_breadcrumbs_target": jina_breadcrumbs_target.strip() if jina_breadcrumbs_target else None,
                    "jina_filters_target": jina_filters_target.strip() if jina_filters_target else None,
                }
                if update_campaign(camp_id, data):
                    st.success("Zapisano zmiany!")
                    set_view_mode("list")
                    
    if col_btn2.button("Anuluj", use_container_width=True):
        set_view_mode("list")
