import streamlit as st
from utils.constants import DEFAULT_OPERATORS

def require_auth():
    """
    Główna funkcja wymuszająca autoryzację.
    Wymaga najpierw podania poprawnego hasła aplikacji, a następnie wyboru operatora.
    Zwraca True, jeśli proces autoryzacji zakończył się sukcesem,
    w przeciwnym razie przerywa dalsze wykonywanie kodu za pomocą st.stop().
    """
    # 1. Weryfikacja obecności hasła w secrets
    try:
        app_password = st.secrets["APP_PASSWORD"]
    except KeyError:
        st.error("🚨 Błąd krytyczny: Brak konfiguracji 'APP_PASSWORD' w pliku .streamlit/secrets.toml.")
        st.info("Dodaj hasło w pliku konfiguracyjnym, aby umożliwić logowanie do aplikacji.")
        st.stop()

    # 2. Sprawdzenie, czy użytkownik jest połączony (zna hasło)
    if not st.session_state.get("is_authenticated", False):
        _show_login_screen(app_password)
        st.stop()

    # 3. Sprawdzenie, czy wybrano operatora
    if not st.session_state.get("current_operator"):
        _show_operator_selection()
        st.stop()

    # Jeśli program doszedł tutaj, znaczy że wszystko jest poprawnie wypełnione
    return True

def _show_login_screen(app_password):
    """Wyświetla ekran logowania dla głównego hasła aplikacji."""
    st.title("Wymagane logowanie")
    st.write("Podaj hasło dostępowe, aby korzystać z generatora treści AI.")

    with st.form("login_form"):
        password_input = st.text_input("Hasło:", type="password")
        submit = st.form_submit_button("Zaloguj", type="primary")

        if submit:
            if password_input == app_password:
                st.session_state["is_authenticated"] = True
                st.rerun()
            else:
                st.error("😕 Nieprawidłowe hasło. Spróbuj ponownie.")

def _show_operator_selection():
    """Wyświetla ekran wyboru operatora pobieranego z secrets lub domyślnej listy."""
    st.title("Wybierz operatora")
    st.write("Kim dzisiaj jesteś? Twój wybór zostanie przypisany do nowych kampanii i zadań.")

    # Pobieranie operatorów z secrets z fallbackiem na constants
    operators_list = st.secrets.get("OPERATORS", DEFAULT_OPERATORS)
    
    with st.form("operator_selection_form"):
        # Dodanie sztucznej opcji jako blokady
        options = ["Wybierz..."] + list(operators_list)
        selected_operator = st.selectbox("Twoje imię:", options)
        submit = st.form_submit_button("Kontynuuj", type="primary")

        if submit:
            if selected_operator != "Wybierz...":
                st.session_state["current_operator"] = selected_operator
                st.rerun()
            else:
                st.error("🚨 Musisz wybrać operatora z listy, aby przejść dalej.")

def logout():
    """Czyści stan autoryzacji z session_state w celu wylogowania."""
    st.session_state["is_authenticated"] = False
    st.session_state["current_operator"] = None
    st.rerun()
