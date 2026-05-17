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
    import_xlsx, queue, results, export, settings
)

def main():
    # 1. Inicjalizacja niezbędnych zmiennych w session_state
    init_session_state()

    # 2. Wymuszenie autoryzacji
    # Jeśli użytkownik nie jest zalogowany lub nie podał operatora,
    # to require_auth samo "zatrzyma" kod wyświetlając formularz logowania.
    require_auth()

    # 3. Jeśli kod wykonuje się dalej, użytkownik jest autoryzowany. 
    # Budujemy boczny pasek i główne menu.
    with st.sidebar:
        st.write(f"Zalogowano jako: **{st.session_state['current_operator']}**")
        
        # Przycisk wylogowania
        if st.button("Wyloguj", type="secondary", use_container_width=True):
            logout()
            
        st.divider()
        st.subheader("Nawigacja")
        
        # Słownik dostępnych widoków aplikacji
        menu_options = {
            "📊 Dashboard": dashboard.render,
            "📂 Kampanie": campaigns.render,
            "🎯 Strategia treści": strategy.render,
            "📝 Prompty": prompts.render,
            "➕ Nowe zadanie": new_job.render,
            "📥 Import XLSX": import_xlsx.render,
            "⚙️ Kolejka": queue.render,
            "✅ Wyniki": results.render,
            "📤 Eksport": export.render,
            "🔧 Ustawienia": settings.render
        }
        
        # Wybór modułu przez użytkownika z radia 
        selected_page = st.radio(
            "Wybierz moduł:", 
            list(menu_options.keys()), 
            label_visibility="collapsed"
        )

    # Uruchomienie wybranej strony
    menu_options[selected_page]()

if __name__ == "__main__":
    main()
