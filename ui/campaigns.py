import streamlit as st
from services.campaign_service import get_campaigns, get_campaign_by_id, create_campaign, update_campaign, archive_campaign
from services.jina_service import fetch_jina_content
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
        
    with st.expander("Integracja Jina AI (Web Scraping)", expanded=False):
        c_jeng, c_jret = st.columns(2)
        jina_engine = c_jeng.selectbox("Silnik (Engine)", ["cf-browser-rendering", "playwright", "default"], index=0, help="Silnik używany przez Jina do omijania zabezpieczeń.", key="new_camp_jeng")
        jina_retain_images = c_jret.selectbox("Retain Images", ["none", "all", "block"], index=0, help="Domyślnie 'none', by zaoszczędzić tokeny.", key="new_camp_jret")
        
        st.markdown("##### Scrapowanie Kategorii")
        c_j1, c_j2 = st.columns(2)
        jina_category_target = c_j1.text_input("Category Target Selector", placeholder=".brand-list-wrapper", key="new_camp_jct")
        jina_category_remove = c_j2.text_input("Category Remove Selector", placeholder=".refinement-content, .add-to-cart", key="new_camp_jcr")
        
        st.markdown("##### Scrapowanie Produktów")
        p_j1, p_j2 = st.columns(2)
        jina_product_target = p_j1.text_input("Product Target Selector", placeholder='#description [itemprop="description"]', key="new_camp_jpt")
        jina_product_remove = p_j2.text_input("Product Remove Selector", placeholder=".related-products", key="new_camp_jpr")
        
        st.markdown("##### Breadcrumbs i Filtry")
        bf_1, bf_2 = st.columns(2)
        jina_breadcrumbs_target = bf_1.text_input("Breadcrumbs Target", placeholder=".breadcrumbs", key="new_camp_jbt")
        jina_filters_target = bf_2.text_input("Filters Target", placeholder=".filters-wrapper", key="new_camp_jft")
        
        st.markdown("---")
        st.markdown("##### 🧪 Tester Selektorów JINA")
        st.caption("Podaj URL sklepu, by przetestować jak JINA widzi Twoje selektory zanim uruchomisz potężne scrapowanie.")
        test_url = st.text_input("URL strony do przetestowania:", placeholder="https://mediamarkt.pl/...", key="new_camp_jtest_url")
        test_selector = st.text_input("Selektor do sprawdzenia (np. z powyższych):", placeholder=".breadcrumbs", key="new_camp_jtest_sel")
        if st.button("Sprawdź Selektor"):
            if not test_url or not test_selector:
                st.warning("Podaj adres URL i selektor do przetestowania.")
            else:
                with st.spinner("Odpytywanie Jina AI..."):
                    j_key = st.secrets.get("JINA_API_KEY") if hasattr(st, "secrets") else None
                    if not j_key:
                        st.error("Brak klucza JINA_API_KEY w secrets.toml!")
                    else:
                        out = fetch_jina_content(test_url.strip(), j_key, jina_engine, test_selector.strip(), None, jina_retain_images)
                        if out:
                            st.success("✅ Udało się pobrać dane!")
                            st.code(out, language="markdown")
                        else:
                            st.error("❌ Pusty wynik lub błąd. JINA nie znalazła tego elementu na stronie lub zablokowano dostęp.")
    
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
        
        st.markdown("##### Scrapowanie Kategorii")
        c_j1, c_j2 = st.columns(2)
        jina_category_target = c_j1.text_input("Category Target Selector", value=camp.get("jina_category_target") or "", placeholder=".brand-list-wrapper", key="edit_camp_jct")
        jina_category_remove = c_j2.text_input("Category Remove Selector", value=camp.get("jina_category_remove") or "", placeholder=".refinement-content, .add-to-cart", key="edit_camp_jcr")
        
        st.markdown("##### Scrapowanie Produktów")
        p_j1, p_j2 = st.columns(2)
        jina_product_target = p_j1.text_input("Product Target Selector", value=camp.get("jina_product_target") or "", placeholder='#description [itemprop="description"]', key="edit_camp_jpt")
        jina_product_remove = p_j2.text_input("Product Remove Selector", value=camp.get("jina_product_remove") or "", placeholder=".related-products", key="edit_camp_jpr")
        
        st.markdown("##### Breadcrumbs i Filtry")
        bf_1, bf_2 = st.columns(2)
        jina_breadcrumbs_target = bf_1.text_input("Breadcrumbs Target", value=camp.get("jina_breadcrumbs_target") or "", placeholder=".breadcrumbs", key="edit_camp_jbt")
        jina_filters_target = bf_2.text_input("Filters Target", value=camp.get("jina_filters_target") or "", placeholder=".filters-wrapper", key="edit_camp_jft")
        
        st.markdown("---")
        st.markdown("##### 🧪 Tester Selektorów JINA")
        st.caption("Podaj URL sklepu, by przetestować jak JINA widzi Twoje selektory zanim uruchomisz potężne scrapowanie.")
        test_url = st.text_input("URL strony do przetestowania:", placeholder="https://mediamarkt.pl/...", key="edit_camp_jtest_url")
        test_selector = st.text_input("Selektor do sprawdzenia (np. z powyższych):", placeholder=".breadcrumbs", key="edit_camp_jtest_sel")
        if st.button("Sprawdź Selektor"):
            if not test_url or not test_selector:
                st.warning("Podaj adres URL i selektor do przetestowania.")
            else:
                with st.spinner("Odpytywanie Jina AI..."):
                    j_key = st.secrets.get("JINA_API_KEY") if hasattr(st, "secrets") else None
                    if not j_key:
                        st.error("Brak klucza JINA_API_KEY w secrets.toml!")
                    else:
                        out = fetch_jina_content(test_url.strip(), j_key, jina_engine, test_selector.strip(), None, jina_retain_images)
                        if out:
                            st.success("✅ Udało się pobrać dane!")
                            st.code(out, language="markdown")
                        else:
                            st.error("❌ Pusty wynik lub błąd. JINA nie znalazła tego elementu na stronie lub zablokowano dostęp.")
    
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
