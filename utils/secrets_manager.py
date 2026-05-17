import streamlit as st
import logging
import os

# Konfiguracja bazowego loggera dla całej aplikacji (do konsoli, nie pliku, bo chmura)
# Używamy standardowego loggera Pythona, który działa świetnie w Streamlit.
logger = logging.getLogger("ai_content_generator")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

def censor_secret(secret_val: str) -> str:
    """Zwraca ukrytą wersję sekretu do logów (np. 'sk-123***')."""
    if not secret_val:
        return "None"
    if len(secret_val) <= 6:
        return "***"
    return f"{secret_val[:4]}...{secret_val[-2:]}"

def get_missing_critical_secrets():
    """Zwraca listę brakujących KRYTYCZNYCH sekretów (uniemożliwiających start app)."""
    missing = []
    
    if "APP_PASSWORD" not in st.secrets or not st.secrets["APP_PASSWORD"]:
        missing.append("APP_PASSWORD")
    if "OPERATORS" not in st.secrets or not st.secrets["OPERATORS"]:
        missing.append("OPERATORS")
    if "SUPABASE_URL" not in st.secrets or not st.secrets["SUPABASE_URL"]:
        missing.append("SUPABASE_URL")
    if "SUPABASE_KEY" not in st.secrets or not st.secrets["SUPABASE_KEY"]:
        missing.append("SUPABASE_KEY")
        
    return missing

def get_missing_api_keys():
    """Zwraca listę brakujących opcjonalnych API keys."""
    missing = []
    
    if "OPENAI_API_KEY" not in st.secrets or not st.secrets["OPENAI_API_KEY"]:
        missing.append("OPENAI_API_KEY")
    if "OPENROUTER_API_KEY" not in st.secrets or not st.secrets["OPENROUTER_API_KEY"]:
        missing.append("OPENROUTER_API_KEY")
        
    return missing
