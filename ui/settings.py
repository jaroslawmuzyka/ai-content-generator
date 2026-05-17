import streamlit as st
from db.supabase_client import check_supabase_connection
from services.prompt_service import seed_default_prompts
from utils.constants import PROVIDERS, MODELS_BY_PROVIDER
from services.ai_service import generate_ai_response

def render():
    st.title("Ustawienia i Diagnostyka")
    st.write("Skonfiguruj i przetestuj połączenia z systemami zewnętrznymi przed startem pracy.")
    
    tab1, tab2, tab3 = st.tabs(["🗄️ Baza Danych", "🤖 AI & Modele", "🌱 Prompty Bazowe"])
    
    with tab1:
        st.subheader("Supabase Connection")
        st.write("Sprawdź poprawność konfiguracji kluczy w st.secrets oraz dostępność bazy.")
        if st.button("🔌 Testuj połączenie z bazą", type="primary"):
            with st.spinner("Sprawdzam połączenie..."):
                is_connected, message = check_supabase_connection()
                if is_connected:
                    st.success(message, icon="✅")
                else:
                    st.error(message, icon="🚨")
                    st.info(
                        "Aby połączenie zadziałało, upewnij się, że w pliku .streamlit/secrets.toml podałeś:\n"
                        "- SUPABASE_URL\n"
                        "- SUPABASE_KEY\n"
                        "Oraz czy wykonałeś skrypt `schema.sql` w edytorze SQL Supabase."
                    )
    
    with tab2:
        st.subheader("Tester Komunikacji AI")
        st.write("Wykorzystaj to narzędzie, aby sprawdzić czy klucze API (OpenAI / OpenRouter) w `st.secrets` działają bezbłędnie.")
        
        c1, c2 = st.columns(2)
        provider = c1.selectbox("Wybierz dostawcę", PROVIDERS, key="test_prov")
        model = c2.selectbox("Wybierz model", MODELS_BY_PROVIDER.get(provider, []), key="test_mod")
        
        sys_prompt = st.text_input("System Prompt (opcjonalnie)", value="Jesteś zwięzłym, zabawnym robotem.", key="test_sys")
        usr_prompt = st.text_area("User Prompt", value="Opisz w dwóch zdaniach dlaczego optymalizacja SEO jest ważna.", key="test_usr")
        
        if st.button("🚀 Wyślij zapytanie testowe", type="primary"):
            with st.spinner(f"Wysyłam pakiety do {provider.upper()}..."):
                res = generate_ai_response(
                    provider=provider,
                    model=model,
                    system_prompt=sys_prompt,
                    user_prompt=usr_prompt,
                    temperature=0.7,
                    max_tokens=250
                )
                
                if res["success"]:
                    st.success("Test zakończony sukcesem! Połączenie prawidłowe.", icon="✅")
                    st.markdown("#### Odpowiedź od modelu:")
                    st.info(res["text"])
                    st.caption(f"**Zużycie tokenów** | Input (prompt): `{res.get('input_tokens')}` | Output (generacja): `{res.get('output_tokens')}`")
                else:
                    st.error("Wystąpił błąd podczas komunikacji z API:", icon="🚨")
                    st.code(res["error"])

    with tab3:
        st.subheader("Domyślne Prompty (Baza Fabryczna)")
        st.write("Skrypt ładujący wstępną (seed) konfigurację 10 kroków generowania dla 4 różnych typów treści. Użyj tego przycisku po świeżej instalacji bazy.")
        
        if st.button("🌱 Zainicjuj Domyślne Prompty", type="secondary"):
            with st.spinner("Ładowanie do bazy..."):
                success, msg = seed_default_prompts()
                if success:
                    st.success(msg, icon="✅")
                else:
                    st.error(msg, icon="🚨")
