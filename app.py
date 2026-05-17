import streamlit as st

# set_page_config zawsze musi znajdować się na samej górze pliku,
# przed uruchomieniem jakichkolwiek innych poleceń interfejsu (z wyjątkiem importów)
st.set_page_config(
    page_title="AI Content Generator",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

from core.auth import require_auth, logout
from core.session import init_session_state

# Importy widoków
from ui import (
    dashboard, campaigns, strategy, prompts, new_job, 
    import_xlsx, queue, results, export, settings, prompt_lab
)

from utils.secrets_manager import get_missing_critical_secrets, get_missing_api_keys

def main():
    # 0. Weryfikacja krytycznych sekretów
    missing_critical = get_missing_critical_secrets()
    if missing_critical:
        st.error("Błąd krytyczny: Brak wymaganych sekretów w pliku `.streamlit/secrets.toml`.")
        st.warning(f"Brakujące klucze: {', '.join(missing_critical)}")
        st.info("Skonfiguruj plik secrets.toml zgodnie z dokumentacją (README.md), aby uruchomić aplikację.")
        st.stop()
        
    # 1. Inicjalizacja niezbędnych zmiennych w session_state
    init_session_state()

    # Weryfikacja opcjonalnych API keys
    missing_api = get_missing_api_keys()
    if missing_api:
        st.session_state["missing_api_keys"] = missing_api
    else:
        st.session_state["missing_api_keys"] = []

    # 2. Wymuszenie autoryzacji
    # Jeśli użytkownik nie jest zalogowany lub nie podał operatora,
    # to require_auth samo "zatrzyma" kod wyświetlając formularz logowania.
    require_auth()

    # 3. Jeśli kod wykonuje się dalej, użytkownik jest autoryzowany. 
    # Budujemy boczny pasek i główne menu.
    with st.sidebar:
        st.write(f"👤 Zalogowano jako: **{st.session_state['current_operator']}**")
        st.divider()
        
        # Szybki wybór aktywnej kampanii
        from services.campaign_service import get_campaigns
        active_camps = get_campaigns("active")
        
        if active_camps:
            camp_opts = {c["id"]: c["name"] for c in active_camps}
            current_active = st.session_state.get('active_campaign_id')
            
            # Zabezpieczenie przed usuniętymi
            if current_active not in camp_opts:
                current_active = None
                
            idx = list(camp_opts.keys()).index(current_active) if current_active else 0
            
            selected_camp = st.selectbox(
                "🎯 Aktywna Kampania", 
                options=[""] + list(camp_opts.keys()) if not current_active else list(camp_opts.keys()),
                format_func=lambda x: camp_opts[x] if x else "--- Wybierz ---",
                index=idx if current_active else 0
            )
            
            if selected_camp and selected_camp != current_active:
                st.session_state['active_campaign_id'] = selected_camp
                st.rerun()
        else:
            st.warning("Brak aktywnych kampanii w systemie.")
            
        st.divider()
        st.subheader("Nawigacja")
        
        # Słownik dostępnych widoków aplikacji
        menu_options = {
            "📊 Panel główny": dashboard.render,
            "📂 Kampanie": campaigns.render,
            "🎯 Strategia treści": strategy.render,
            "📝 Prompty": prompts.render,
            "➕ Nowa treść": new_job.render,
            "📥 Import XLSX": import_xlsx.render,
            "⚙️ Kolejka generowania": queue.render,
            "✅ Wyniki treści": results.render,
            "📤 Eksport": export.render,
            "🧪 Doskonal prompty": prompt_lab.render,
            "🔧 Ustawienia": settings.render
        }
        
        # Wybór modułu przez użytkownika z radia 
        selected_page = st.radio(
            "Wybierz moduł:", 
            list(menu_options.keys()), 
            label_visibility="collapsed"
        )
        
        st.write("")
        st.write("")
        # Przycisk wylogowania na samym dole
        if st.button("🚪 Wyloguj", type="secondary", use_container_width=True):
            logout()

    # Uruchomienie wybranej strony
    menu_options[selected_page]()

if __name__ == "__main__":
    main()
